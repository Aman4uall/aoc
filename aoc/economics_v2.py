from __future__ import annotations

from aoc.models import (
    AlternativeOption,
    CalcTrace,
    ColumnDesign,
    CostModel,
    DebtSchedule,
    DebtScheduleEntry,
    DecisionCriterion,
    DecisionRecord,
    EconomicScenarioModel,
    EquipmentCostItem,
    EquipmentCostBreakdown,
    EquipmentSpec,
    FinancialModel,
    FinancialSchedule,
    FinancialScheduleLine,
    IndianPriceDatum,
    MarketAssessmentArtifact,
    OperationsPlanningArtifact,
    PlantCostSummary,
    ProcurementPackageImpact,
    ProjectBasis,
    RouteEconomicBasisArtifact,
    RouteEconomicItem,
    RouteSelectionArtifact,
    RouteSiteFitArtifact,
    ScenarioStability,
    ScenarioPolicy,
    ScenarioResult,
    SensitivityLevel,
    SiteSelectionArtifact,
    StreamTable,
    TaxDepreciationBasis,
    UtilityIslandEconomicImpact,
    UtilityIslandScenarioImpact,
    UtilityArchitectureDecision,
    UtilitySummaryArtifact,
    WorkingCapitalModel,
    FlowsheetBlueprintArtifact,
)
from aoc.value_engine import make_value_record


def _annual_output_kg(basis: ProjectBasis) -> float:
    return basis.capacity_tpa * 1000.0


def _operating_hours(basis: ProjectBasis) -> float:
    return basis.annual_operating_days * 24.0


def _find_price(price_data: list[IndianPriceDatum], item_name: str, default: float) -> float:
    for datum in price_data:
        if datum.item_name.lower() == item_name.lower():
            return datum.value_inr
    return default


def _sum_utility_load(utilities: UtilitySummaryArtifact, prefix: str) -> float:
    lowered = prefix.lower()
    return sum(item.load for item in utilities.items if item.utility_type.lower().startswith(lowered))


def _selected_location_datum(site: SiteSelectionArtifact):
    for location in site.india_location_data:
        if location.site_name.lower() == site.selected_site.lower():
            return location
    return site.india_location_data[0] if site.india_location_data else None


def _component_molecular_weight_lookup(stream_table: StreamTable) -> dict[str, float]:
    lookup: dict[str, float] = {}
    for stream in stream_table.streams:
        for component in stream.components:
            if component.molar_flow_kmol_hr > 1e-12:
                lookup.setdefault(component.name, component.mass_flow_kg_hr / component.molar_flow_kmol_hr)
    return lookup


def _fresh_makeup_mass_kg_hr(stream_table: StreamTable) -> float:
    explicit_feed_mass = sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_role == "feed"
        for component in stream.components
    )
    if explicit_feed_mass > 0.0:
        return explicit_feed_mass
    if not stream_table.recycle_packets:
        return 0.0
    molecular_weights = _component_molecular_weight_lookup(stream_table)
    loop_components: set[str] = set()
    loop_fresh_mass = 0.0
    for packet in stream_table.recycle_packets:
        for component_name, fresh_kmol_hr in packet.component_fresh_kmol_hr.items():
            mw = molecular_weights.get(component_name, 0.0)
            if mw <= 0.0:
                continue
            loop_components.add(component_name)
            loop_fresh_mass += fresh_kmol_hr * mw
    non_loop_feed_mass = sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_role == "feed"
        for component in stream.components
        if component.name not in loop_components
    )
    return loop_fresh_mass + non_loop_feed_mass


def _blueprint_metrics(flowsheet_blueprint: FlowsheetBlueprintArtifact | None) -> tuple[int, int, int, bool]:
    if flowsheet_blueprint is None:
        return 0, 0, 0, False
    return (
        len(flowsheet_blueprint.steps),
        len(flowsheet_blueprint.separation_duties),
        len(flowsheet_blueprint.recycle_intents),
        flowsheet_blueprint.batch_capable,
    )


def build_route_site_fit_artifact(
    basis: ProjectBasis,
    site: SiteSelectionArtifact,
    route_selection: RouteSelectionArtifact,
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None,
    operations_planning: OperationsPlanningArtifact,
    citations: list[str],
    assumptions: list[str],
) -> RouteSiteFitArtifact:
    location = _selected_location_datum(site)
    site_name = site.selected_site
    lower_port_note = (location.port_access.lower() if location is not None else "")
    coastal = "port" in lower_port_note or site_name.lower() in {"dahej", "jamnagar", "paradip", "mangalore", "vizag"}
    blueprint_step_count, separation_duty_count, recycle_intent_count, batch_capable = _blueprint_metrics(flowsheet_blueprint)
    complexity_index = max(blueprint_step_count - 4, 0) + separation_duty_count + recycle_intent_count
    port_dependency_factor = min(
        0.10 + 0.05 * separation_duty_count + 0.04 * recycle_intent_count + 0.015 * max(blueprint_step_count - 5, 0),
        0.85,
    )
    feedstock_cluster_factor = 1.0 + 0.012 * recycle_intent_count + 0.008 * max(blueprint_step_count - 5, 0)
    if not coastal and not batch_capable:
        feedstock_cluster_factor += 0.035
    logistics_penalty_factor = 1.0 + (0.020 if coastal else 0.060) + port_dependency_factor * (0.020 if coastal else 0.085)
    utility_reliability_factor = 1.0 + 0.010 * separation_duty_count + (0.008 if not coastal and complexity_index >= 3 else 0.0)
    batch_site_factor = 0.97 if batch_capable and not coastal else 1.04 if batch_capable else 1.0
    overall_fit_score = max(
        55.0,
        92.0
        - max(feedstock_cluster_factor - 1.0, 0.0) * 120.0
        - max(logistics_penalty_factor - 1.0, 0.0) * 90.0
        - max(utility_reliability_factor - 1.0, 0.0) * 80.0
        + (3.0 if batch_capable and not coastal else 0.0),
    )
    notes = (
        f"Selected site `{site_name}` is screened against blueprint complexity "
        f"({blueprint_step_count} steps, {separation_duty_count} separation duties, {recycle_intent_count} recycle intents) "
        f"for route `{route_selection.selected_route_id}`."
    )
    if batch_capable:
        notes += f" Batch-capable route handling uses `{operations_planning.availability_policy_label}` to soften inland penalties where appropriate."
    markdown = "\n".join(
        [
            "| Metric | Value |",
            "| --- | --- |",
            f"| Selected site | {site_name} |",
            f"| Route | {route_selection.selected_route_id} |",
            f"| Blueprint steps | {blueprint_step_count} |",
            f"| Separation duties | {separation_duty_count} |",
            f"| Recycle intents | {recycle_intent_count} |",
            f"| Batch-capable | {'yes' if batch_capable else 'no'} |",
            f"| Port dependency factor | {port_dependency_factor:.3f} |",
            f"| Feedstock cluster factor | {feedstock_cluster_factor:.3f} |",
            f"| Logistics penalty factor | {logistics_penalty_factor:.3f} |",
            f"| Utility reliability factor | {utility_reliability_factor:.3f} |",
            f"| Batch-site factor | {batch_site_factor:.3f} |",
            f"| Overall site-fit score | {overall_fit_score:.2f} |",
        ]
    )
    return RouteSiteFitArtifact(
        route_id=route_selection.selected_route_id,
        selected_site=site_name,
        blueprint_id=flowsheet_blueprint.blueprint_id if flowsheet_blueprint is not None else "",
        blueprint_step_count=blueprint_step_count,
        separation_duty_count=separation_duty_count,
        recycle_intent_count=recycle_intent_count,
        batch_capable=batch_capable,
        port_dependency_factor=round(port_dependency_factor, 6),
        feedstock_cluster_factor=round(feedstock_cluster_factor, 6),
        logistics_penalty_factor=round(logistics_penalty_factor, 6),
        utility_reliability_factor=round(utility_reliability_factor, 6),
        batch_site_factor=round(batch_site_factor, 6),
        overall_fit_score=round(overall_fit_score, 3),
        notes=notes,
        markdown=markdown,
        citations=citations,
        assumptions=assumptions + ["Route site-fit screening couples selected site data to route blueprint complexity rather than using site label alone."],
    )


def build_route_economic_basis_artifact(
    basis: ProjectBasis,
    site: SiteSelectionArtifact,
    route_selection: RouteSelectionArtifact,
    stream_table: StreamTable,
    market: MarketAssessmentArtifact,
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None,
    operations_planning: OperationsPlanningArtifact,
    route_site_fit: RouteSiteFitArtifact,
    citations: list[str],
    assumptions: list[str],
) -> RouteEconomicBasisArtifact:
    blueprint_step_count, separation_duty_count, recycle_intent_count, batch_capable = _blueprint_metrics(flowsheet_blueprint)
    annual_hours = _operating_hours(basis)
    feed_components = {
        component.name
        for stream in stream_table.streams
        if stream.stream_role == "feed"
        for component in stream.components
    }
    recycle_component_count = len(
        {
            component.name
            for stream in stream_table.streams
            if stream.stream_role == "recycle"
            for component in stream.components
        }
    )
    feed_component_count = len(feed_components)
    raw_material_complexity_factor = 1.0 + 0.020 * max(feed_component_count - 1, 0) + 0.012 * recycle_intent_count + 0.010 * separation_duty_count
    site_input_cost_factor = route_site_fit.feedstock_cluster_factor * (1.0 + route_site_fit.port_dependency_factor * 0.04)
    logistics_intensity_factor = 1.0 + 0.015 * max(blueprint_step_count - 5, 0) + 0.020 * separation_duty_count + route_site_fit.port_dependency_factor * 0.05
    batch_occupancy_penalty_fraction = 0.0
    if batch_capable or basis.operating_mode == "batch":
        batch_occupancy_penalty_fraction = min(
            0.030
            + 0.006 * max(blueprint_step_count - 4, 0)
            + 0.004 * separation_duty_count
            + max(operations_planning.cleaning_downtime_days, 0.0) / max(operations_planning.campaign_length_days, 1.0) * 0.60,
            0.22,
        )
    recycle_mass_kg_hr = sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_role == "recycle"
        for component in stream.components
    )
    solvent_recovery_service_cost_inr = recycle_mass_kg_hr * annual_hours * 0.04 * (0.60 + 0.25 * separation_duty_count)
    catalyst_hint = " ".join(step.service.lower() for step in (flowsheet_blueprint.steps if flowsheet_blueprint is not None else []))
    catalyst_service_cost_inr = (
        annual_hours * (250.0 + 80.0 * recycle_intent_count)
        if any(token in catalyst_hint for token in ("catalyst", "converter", "fixed-bed", "reactor"))
        else 0.0
    )
    waste_flow_kg_hr = sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_role in {"waste", "vent", "purge"}
        for component in stream.components
    )
    waste_treatment_burden_inr = waste_flow_kg_hr * annual_hours * 0.02 * (1.0 + 0.20 * separation_duty_count)
    coverage_status = "grounded" if market.india_price_data and route_site_fit.overall_fit_score >= 75.0 else "hybrid" if market.india_price_data else "screening"
    items = [
        RouteEconomicItem(
            component_name=", ".join(sorted(feed_components)) or basis.target_product,
            role="raw_materials",
            annualized_burden_inr=round(raw_material_complexity_factor * site_input_cost_factor, 6),
            notes="Composite feedstock complexity and selected-site input-cost multiplier.",
            citations=citations,
            assumptions=assumptions,
        ),
        RouteEconomicItem(
            component_name="Recycle / solvent recovery",
            role="service",
            annualized_burden_inr=round(solvent_recovery_service_cost_inr, 2),
            recovery_fraction=min(0.95, 0.30 + 0.08 * recycle_intent_count),
            notes="Annualized service burden from recycle-heavy route handling.",
            citations=citations,
            assumptions=assumptions,
        ),
        RouteEconomicItem(
            component_name="Catalyst / reactor service",
            role="service",
            annualized_burden_inr=round(catalyst_service_cost_inr, 2),
            notes="Annualized recurring burden from catalyst/converter style service where inferred.",
            citations=citations,
            assumptions=assumptions,
        ),
        RouteEconomicItem(
            component_name="Waste treatment",
            role="waste",
            annualized_burden_inr=round(waste_treatment_burden_inr, 2),
            notes="Annualized waste and purge burden from route-derived waste streams.",
            citations=citations,
            assumptions=assumptions,
        ),
    ]
    markdown = "\n".join(
        [
            "| Metric | Value |",
            "| --- | --- |",
            f"| Route | {route_selection.selected_route_id} |",
            f"| Selected site | {site.selected_site} |",
            f"| Operating mode | {basis.operating_mode} |",
            f"| Blueprint steps | {blueprint_step_count} |",
            f"| Separation duties | {separation_duty_count} |",
            f"| Recycle intents | {recycle_intent_count} |",
            f"| Major feed components | {', '.join(sorted(feed_components)) or '-'} |",
            f"| Recycle component count | {recycle_component_count} |",
            f"| Raw-material complexity factor | {raw_material_complexity_factor:.3f} |",
            f"| Site input-cost factor | {site_input_cost_factor:.3f} |",
            f"| Logistics intensity factor | {logistics_intensity_factor:.3f} |",
            f"| Batch occupancy penalty | {batch_occupancy_penalty_fraction:.3f} |",
            f"| Solvent recovery service | {solvent_recovery_service_cost_inr:,.2f} INR/y |",
            f"| Catalyst service | {catalyst_service_cost_inr:,.2f} INR/y |",
            f"| Waste treatment burden | {waste_treatment_burden_inr:,.2f} INR/y |",
            f"| Coverage status | {coverage_status} |",
        ]
    )
    return RouteEconomicBasisArtifact(
        route_id=route_selection.selected_route_id,
        selected_site=site.selected_site,
        blueprint_id=flowsheet_blueprint.blueprint_id if flowsheet_blueprint is not None else "",
        operating_mode=basis.operating_mode,
        blueprint_step_count=blueprint_step_count,
        separation_duty_count=separation_duty_count,
        recycle_intent_count=recycle_intent_count,
        batch_capable=batch_capable,
        major_feed_components=sorted(feed_components),
        recycle_component_count=recycle_component_count,
        raw_material_complexity_factor=round(raw_material_complexity_factor, 6),
        site_input_cost_factor=round(site_input_cost_factor, 6),
        logistics_intensity_factor=round(logistics_intensity_factor, 6),
        batch_occupancy_penalty_fraction=round(batch_occupancy_penalty_fraction, 6),
        solvent_recovery_service_cost_inr=round(solvent_recovery_service_cost_inr, 2),
        catalyst_service_cost_inr=round(catalyst_service_cost_inr, 2),
        waste_treatment_burden_inr=round(waste_treatment_burden_inr, 2),
        coverage_status=coverage_status,
        items=items,
        notes="Route-derived economics now uses selected-site fit, stream recycle burden, and blueprint complexity to adjust cost realism.",
        markdown=markdown,
        citations=citations,
        assumptions=assumptions + ["Route-derived economics uses stream-table feed/recycle/waste burdens and blueprint complexity instead of route label alone."],
    )


def _equipment_cost_terms(
    item: EquipmentSpec,
    column_design: ColumnDesign | None,
) -> tuple[float, float, float, list[str], float]:
    lower_type = item.equipment_type.lower()
    installed_multiplier = 2.00 if "storage" in lower_type else 2.25
    spares_fraction = 0.03 if "pump" in lower_type else 0.015
    capex_multiplier = 1.0
    note_lines: list[str] = []
    annual_service_cost = 0.0
    if column_design is None:
        return capex_multiplier, installed_multiplier, spares_fraction, note_lines, annual_service_cost
    if lower_type == "packing internals" and "absorption" in column_design.service.lower():
        structured = column_design.absorber_packing_family.startswith("structured")
        family_multiplier = 1.30 if structured else 0.96
        specific_area_multiplier = 1.0 + max(column_design.absorber_packing_specific_area_m2_m3 - 125.0, 0.0) / 125.0 * 0.18
        hydraulic_multiplier = 1.0 + min(column_design.absorber_total_pressure_drop_kpa / 20.0, 1.8) * 0.12
        window_multiplier = 1.0 + max(1.0 - column_design.absorber_wetting_ratio, 0.0) * 0.22 + max(0.20 - column_design.absorber_flooding_margin_fraction, 0.0) * 1.10
        capex_multiplier = family_multiplier * specific_area_multiplier * hydraulic_multiplier * window_multiplier
        installed_multiplier = 2.35
        spares_fraction = 0.030 if structured else 0.022
        annual_service_cost = (
            0.011
            + (0.005 if structured else 0.003)
            + min(column_design.absorber_pressure_drop_per_m_kpa_m / 4.0, 1.0) * 0.003
            + max(1.0 - column_design.absorber_wetting_ratio, 0.0) * 0.006
        )
        note_lines.append(
            f"Packing-family CAPEX multiplier {capex_multiplier:.3f} from {column_design.absorber_packing_family}, "
            f"specific area {column_design.absorber_packing_specific_area_m2_m3:.1f} m2/m3, "
            f"and hydraulic window (wetting={column_design.absorber_wetting_ratio:.3f}, flooding margin={column_design.absorber_flooding_margin_fraction:.3f})."
        )
    elif lower_type == "crystal classifier" and "crystallizer" in column_design.service.lower():
        cut_size_multiplier = 1.0 + max(0.35 - column_design.crystal_classifier_cut_size_mm, 0.0) / 0.35 * 0.28
        circulation_multiplier = 1.0 + min(column_design.slurry_circulation_rate_m3_hr / 120.0, 2.0) * 0.18
        sharpness_multiplier = 1.0 + max(column_design.crystal_classified_product_fraction - 0.75, 0.0) * 0.20
        capex_multiplier = cut_size_multiplier * circulation_multiplier * sharpness_multiplier
        installed_multiplier = 2.30
        spares_fraction = 0.030
        annual_service_cost = (
            column_design.slurry_circulation_rate_m3_hr
            * 0.9
            * (1.0 + max(0.30 - column_design.crystal_classifier_cut_size_mm, 0.0) / 0.30 * 0.25)
        )
        note_lines.append(
            f"Classifier CAPEX multiplier {capex_multiplier:.3f} from cut size {column_design.crystal_classifier_cut_size_mm:.3f} mm, "
            f"classified fraction {column_design.crystal_classified_product_fraction:.3f}, "
            f"and slurry circulation {column_design.slurry_circulation_rate_m3_hr:.1f} m3/h."
        )
    elif lower_type == "pressure filter" and "crystallizer" in column_design.service.lower():
        area_multiplier = 1.0 + min(column_design.filter_area_m2 / 60.0, 2.0) * 0.18
        cake_multiplier = 1.0 + min(column_design.filter_specific_cake_resistance_m_kg / 1.0e10, 3.0) * 0.16
        medium_multiplier = 1.0 + min(column_design.filter_medium_resistance_1_m / 5.0e10, 2.0) * 0.10
        capex_multiplier = area_multiplier * cake_multiplier * medium_multiplier
        installed_multiplier = 2.40
        spares_fraction = 0.028
        annual_service_cost = (
            column_design.filter_area_m2 * 18000.0
            * (1.0 + min(column_design.filter_specific_cake_resistance_m_kg / 1.0e10, 3.0) * 0.20)
        )
        note_lines.append(
            f"Filter CAPEX multiplier {capex_multiplier:.3f} from area {column_design.filter_area_m2:.1f} m2, "
            f"cake resistance {column_design.filter_specific_cake_resistance_m_kg:.3e} m/kg, "
            f"and medium resistance {column_design.filter_medium_resistance_1_m:.3e} 1/m."
        )
    elif lower_type == "dryer gas handling skid" and "crystallizer" in column_design.service.lower():
        air_multiplier = 1.0 + min(column_design.dryer_dry_air_flow_kg_hr / 50000.0, 2.0) * 0.16
        humidity_multiplier = 1.0 + max(column_design.dryer_exhaust_saturation_fraction - 0.65, 0.0) * 0.45
        endpoint_multiplier = 1.0 + max(
            column_design.dryer_target_moisture_fraction - column_design.dryer_product_moisture_fraction,
            0.0,
        ) / max(column_design.dryer_target_moisture_fraction, 1e-6) * 0.18
        capex_multiplier = air_multiplier * humidity_multiplier * endpoint_multiplier
        installed_multiplier = 2.35
        spares_fraction = 0.025
        annual_service_cost = (
            column_design.dryer_dry_air_flow_kg_hr
            * 0.00045
            * (1.0 + max(column_design.dryer_exhaust_saturation_fraction - 0.65, 0.0) * 1.5)
        )
        note_lines.append(
            f"Dryer gas-handling CAPEX multiplier {capex_multiplier:.3f} from dry-air flow {column_design.dryer_dry_air_flow_kg_hr:.1f} kg/h, "
            f"exhaust saturation {column_design.dryer_exhaust_saturation_fraction:.3f}, "
            f"and endpoint moisture {column_design.dryer_product_moisture_fraction:.4f}."
        )
    return capex_multiplier, installed_multiplier, spares_fraction, note_lines, annual_service_cost


def _availability_policy_for_cost_model(column_design: ColumnDesign | None) -> dict[str, float | int | str]:
    service = (column_design.service.lower() if column_design is not None else "")
    if "absorption" in service:
        return {
            "label": "gas_liquid_absorption_train",
            "minor_outage_days": 4.0,
            "major_turnaround_days": 11.0,
            "startup_loss_days": 2.5,
            "turnaround_cycle_years": 3,
            "turnaround_event_fraction": 0.0038,
            "minor_window_note": "Quarterly absorber wash and acid-circuit inspection windows are consolidated into an annual minor outage allowance.",
            "major_window_note": "A major absorber/regeneration turnaround is assumed in the post-monsoon maintenance window.",
        }
    if "crystallizer" in service or "dryer" in service or "solid" in service:
        return {
            "label": "solids_crystallization_train",
            "minor_outage_days": 6.0,
            "major_turnaround_days": 16.0,
            "startup_loss_days": 4.5,
            "turnaround_cycle_years": 2,
            "turnaround_event_fraction": 0.0055,
            "minor_window_note": "Periodic classifier, filter cloth, and dryer cleanout are represented as annual minor outage windows.",
            "major_window_note": "A solids-handling turnaround is assumed before the high-humidity season to reset filtration and drying hardware.",
        }
    if "distillation" in service or "process unit" in service:
        return {
            "label": "continuous_liquid_organic_train",
            "minor_outage_days": 5.0,
            "major_turnaround_days": 13.0,
            "startup_loss_days": 3.5,
            "turnaround_cycle_years": 4,
            "turnaround_event_fraction": 0.0046,
            "minor_window_note": "Routine exchanger cleaning and column internals inspection are represented as annual minor outages.",
            "major_window_note": "A major process-unit turnaround is assumed in a low-demand maintenance window.",
        }
    return {
        "label": "generic_process_train",
        "minor_outage_days": 4.0,
        "major_turnaround_days": 12.0,
        "startup_loss_days": 3.0,
        "turnaround_cycle_years": 3,
        "turnaround_event_fraction": 0.0042,
        "minor_window_note": "Generic process inspections and cleaning outages are represented as annual downtime.",
        "major_window_note": "A generic major turnaround is assumed at a three-year interval.",
    }


def _procurement_profile_for_cost_model(
    procurement_basis: DecisionRecord,
    equipment: list[EquipmentSpec],
) -> dict[str, float | int | str | list[dict[str, float | str]]]:
    total_items = max(len(equipment), 1)
    long_lead_tokens = (
        "reactor",
        "column",
        "absorber",
        "crystallizer",
        "filter",
        "dryer",
        "exchanger",
        "packing",
    )
    import_tokens = ("compressor", "controls", "packing", "classifier", "filter", "dryer")
    long_lead_count = sum(
        1
        for item in equipment
        if any(token in item.equipment_type.lower() for token in long_lead_tokens)
    )
    import_like_count = sum(
        1
        for item in equipment
        if any(token in item.equipment_type.lower() for token in import_tokens)
    )
    base_profiles = {
        "domestic_cluster_procurement": {
            "label": "domestic_cluster_timing",
            "construction_months": 18,
            "advance_fraction": 0.15,
            "progress_fraction": 0.75,
            "retention_fraction": 0.10,
            "imported_equipment_fraction": 0.14,
            "long_lead_fraction": 0.20,
        },
        "mixed_import_domestic": {
            "label": "mixed_import_timing",
            "construction_months": 20,
            "advance_fraction": 0.20,
            "progress_fraction": 0.70,
            "retention_fraction": 0.10,
            "imported_equipment_fraction": 0.28,
            "long_lead_fraction": 0.30,
        },
        "import_heavy": {
            "label": "import_heavy_timing",
            "construction_months": 22,
            "advance_fraction": 0.25,
            "progress_fraction": 0.65,
            "retention_fraction": 0.10,
            "imported_equipment_fraction": 0.42,
            "long_lead_fraction": 0.36,
        },
    }
    profile = dict(base_profiles.get(procurement_basis.selected_candidate_id or "", base_profiles["mixed_import_domestic"]))
    profile["imported_equipment_fraction"] = min(
        float(profile["imported_equipment_fraction"]) + import_like_count / total_items * 0.10,
        0.78,
    )
    profile["long_lead_fraction"] = min(
        float(profile["long_lead_fraction"]) + long_lead_count / total_items * 0.14,
        0.82,
    )
    profile["construction_months"] = int(
        round(float(profile["construction_months"]) + max(long_lead_count - total_items * 0.30, 0.0))
    )
    progress_fraction = float(profile["progress_fraction"])
    construction_months = max(int(profile["construction_months"]), 12)
    schedule_template = [
        {"milestone": "advance_release", "month": 0.0, "draw_fraction": float(profile["advance_fraction"])},
        {"milestone": "fabrication_progress", "month": round(construction_months * 0.35, 1), "draw_fraction": progress_fraction * 0.42},
        {"milestone": "delivery_release", "month": round(construction_months * 0.65, 1), "draw_fraction": progress_fraction * 0.33},
        {"milestone": "site_erection", "month": round(construction_months * 0.90, 1), "draw_fraction": progress_fraction * 0.25},
        {"milestone": "performance_retention", "month": float(construction_months), "draw_fraction": float(profile["retention_fraction"])},
    ]
    return {
        **profile,
        "schedule_template": schedule_template,
        "note": (
            f"Procurement basis '{procurement_basis.selected_candidate_id or 'mixed_import_domestic'}' implies "
            f"{construction_months} construction months with long-lead fraction {float(profile['long_lead_fraction']):.3f} "
            f"and imported-equipment fraction {float(profile['imported_equipment_fraction']):.3f}."
        ),
    }


def _procurement_package_terms(
    equipment_type: str,
    service: str,
    procurement_profile: dict[str, float | int | str | list[dict[str, float | str]]],
) -> dict[str, float | str | bool | list[tuple[str, float]]]:
    lower_type = equipment_type.lower()
    lower_service = service.lower()
    family = "general_fabrication"
    base_import_fraction = 0.12
    import_duty_fraction = 0.075
    base_lead_months = 6.0
    milestone_fractions: list[tuple[str, float]] = [
        ("advance_release", 0.18),
        ("fabrication_progress", 0.42),
        ("delivery_release", 0.20),
        ("site_erection", 0.10),
        ("performance_retention", 0.10),
    ]
    if any(token in lower_type for token in ("reactor", "column", "absorber", "extract", "flash drum")):
        family = "pressure_vessel_package"
        base_import_fraction = 0.22
        import_duty_fraction = 0.082
        base_lead_months = 10.0
        milestone_fractions = [
            ("advance_release", 0.20),
            ("fabrication_progress", 0.46),
            ("delivery_release", 0.19),
            ("site_erection", 0.05),
            ("performance_retention", 0.10),
        ]
    elif "packing" in lower_type:
        family = "internals_and_packing_package"
        base_import_fraction = 0.58
        import_duty_fraction = 0.105
        base_lead_months = 8.0
        milestone_fractions = [
            ("advance_release", 0.25),
            ("fabrication_progress", 0.36),
            ("delivery_release", 0.21),
            ("site_erection", 0.08),
            ("performance_retention", 0.10),
        ]
    elif any(token in lower_type for token in ("crystallizer", "classifier", "filter", "dryer")) or "crystallizer" in lower_service:
        family = "solids_handling_package"
        base_import_fraction = 0.34
        import_duty_fraction = 0.092
        base_lead_months = 9.0
        milestone_fractions = [
            ("advance_release", 0.22),
            ("fabrication_progress", 0.40),
            ("delivery_release", 0.20),
            ("site_erection", 0.08),
            ("performance_retention", 0.10),
        ]
    elif any(token in lower_type for token in ("heat exchanger", "htm", "thermal")):
        family = "thermal_exchange_package"
        base_import_fraction = 0.18
        import_duty_fraction = 0.078
        base_lead_months = 7.0
    elif any(token in lower_type for token in ("control", "skid", "compressor")):
        family = "instrumented_skid_package"
        base_import_fraction = 0.42
        import_duty_fraction = 0.110
        base_lead_months = 6.0
    elif "storage" in lower_type or "tank" in lower_type:
        family = "tankage_and_balance_of_plant"
        base_import_fraction = 0.04
        import_duty_fraction = 0.040
        base_lead_months = 4.0
        milestone_fractions = [
            ("advance_release", 0.12),
            ("fabrication_progress", 0.48),
            ("delivery_release", 0.20),
            ("site_erection", 0.10),
            ("performance_retention", 0.10),
        ]
    imported_profile = float(procurement_profile["imported_equipment_fraction"])
    long_lead_profile = float(procurement_profile["long_lead_fraction"])
    import_multiplier = 0.82 + imported_profile
    lead_multiplier = 0.88 + long_lead_profile
    import_content_fraction = min(max(base_import_fraction * import_multiplier, 0.02), 0.95)
    lead_time_months = max(base_lead_months * lead_multiplier, 2.5)
    construction_months = max(int(procurement_profile["construction_months"]), 12)
    award_month = max(construction_months - lead_time_months - 1.0, 0.0)
    delivery_month = min(award_month + lead_time_months * 0.82, construction_months * 0.88)
    erection_month = min(max(delivery_month + 0.75, award_month + lead_time_months * 0.94), construction_months * 0.97)
    return {
        "package_family": family,
        "import_content_fraction": round(import_content_fraction, 6),
        "import_duty_fraction": round(import_duty_fraction, 6),
        "lead_time_months": round(lead_time_months, 3),
        "award_month": round(award_month, 2),
        "delivery_month": round(delivery_month, 2),
        "erection_month": round(erection_month, 2),
        "long_lead": lead_time_months >= 7.0,
        "milestone_fractions": milestone_fractions,
    }


def _build_procurement_package_impacts(
    equipment_cost_items: list[EquipmentCostItem],
    procurement_profile: dict[str, float | int | str | list[dict[str, float | str]]],
    total_capex: float,
    citations: list[str],
    assumptions: list[str],
) -> tuple[list[ProcurementPackageImpact], list[dict[str, float | str]], float]:
    installed_total = max(sum(item.installed_cost_inr for item in equipment_cost_items), 1.0)
    schedule_by_key: dict[tuple[str, str, float], dict[str, float | str]] = {}
    impacts: list[ProcurementPackageImpact] = []
    total_import_duty = 0.0
    for item in equipment_cost_items:
        capex_share = item.installed_cost_inr / installed_total
        capex_burden = total_capex * capex_share
        erection_month = min(
            max(item.procurement_delivery_month + 0.75, item.procurement_award_month + item.procurement_lead_time_months * 0.94),
            float(procurement_profile["construction_months"]) * 0.97,
        )
        impacts.append(
            ProcurementPackageImpact(
                package_id=item.equipment_id,
                equipment_type=item.equipment_type,
                package_family=item.procurement_package_family or "general_fabrication",
                lead_time_months=round(item.procurement_lead_time_months, 3),
                award_month=round(item.procurement_award_month, 2),
                delivery_month=round(item.procurement_delivery_month, 2),
                erection_month=round(erection_month, 2),
                import_content_fraction=round(item.import_content_fraction, 6),
                import_duty_fraction=round(item.import_duty_fraction, 6),
                import_duty_inr=round(item.import_duty_inr, 2),
                capex_burden_inr=round(capex_burden, 2),
                long_lead=item.procurement_lead_time_months >= 7.0,
                notes=item.notes,
                citations=item.citations,
                assumptions=item.assumptions,
            )
        )
        total_import_duty += item.import_duty_inr
        milestone_fractions = _procurement_package_terms(item.equipment_type, item.service, procurement_profile)["milestone_fractions"]
        milestone_month_map = {
            "advance_release": item.procurement_award_month,
            "fabrication_progress": round(item.procurement_award_month + item.procurement_lead_time_months * 0.45, 1),
            "delivery_release": item.procurement_delivery_month,
            "site_erection": round(erection_month, 1),
            "performance_retention": float(procurement_profile["construction_months"]),
        }
        for milestone, milestone_fraction in milestone_fractions:
            month = round(float(milestone_month_map[milestone]), 1)
            key = (item.procurement_package_family or "general_fabrication", milestone, month)
            existing = schedule_by_key.setdefault(
                key,
                {
                    "package_family": key[0],
                    "milestone": milestone,
                    "month": month,
                    "draw_fraction": 0.0,
                    "capex_draw_inr": 0.0,
                },
            )
            existing["draw_fraction"] = round(float(existing["draw_fraction"]) + capex_share * milestone_fraction, 6)
            existing["capex_draw_inr"] = round(float(existing["capex_draw_inr"]) + capex_burden * milestone_fraction, 2)
    schedule_rows = sorted(
        schedule_by_key.values(),
        key=lambda row: (float(row["month"]), str(row["package_family"]), str(row["milestone"])),
    )
    return impacts, schedule_rows, round(total_import_duty, 2)


def _financing_terms(financing_basis: DecisionRecord) -> tuple[float, float]:
    interest_rate = {"debt_equity_70_30": 0.105, "debt_equity_60_40": 0.11, "conservative_50_50": 0.12}.get(
        financing_basis.selected_candidate_id or "",
        0.11,
    )
    debt_fraction = {"debt_equity_70_30": 0.70, "debt_equity_60_40": 0.60, "conservative_50_50": 0.50}.get(
        financing_basis.selected_candidate_id or "",
        0.60,
    )
    return interest_rate, debt_fraction


def _coverage_breach_codes(
    minimum_dscr: float,
    average_dscr: float,
    llcr: float,
    plcr: float,
    *,
    has_debt: bool,
) -> list[str]:
    if not has_debt:
        return []
    codes: list[str] = []
    if minimum_dscr < 1.10:
        codes.append("minimum_dscr_breach")
    if average_dscr < 1.25:
        codes.append("average_dscr_breach")
    if llcr < 1.30:
        codes.append("llcr_breach")
    if plcr < 1.45:
        codes.append("plcr_breach")
    return codes


def _breach_warning_messages(
    minimum_dscr: float,
    average_dscr: float,
    llcr: float,
    plcr: float,
    *,
    has_debt: bool,
) -> list[str]:
    warnings: list[str] = []
    for code in _coverage_breach_codes(minimum_dscr, average_dscr, llcr, plcr, has_debt=has_debt):
        if code == "minimum_dscr_breach":
            warnings.append(f"Minimum DSCR {minimum_dscr:.3f} is below the screening covenant threshold of 1.10.")
        elif code == "average_dscr_breach":
            warnings.append(f"Average DSCR {average_dscr:.3f} is below the screening covenant threshold of 1.25.")
        elif code == "llcr_breach":
            warnings.append(f"LLCR {llcr:.3f} is below the screening covenant threshold of 1.30.")
        elif code == "plcr_breach":
            warnings.append(f"PLCR {plcr:.3f} is below the screening covenant threshold of 1.45.")
    return warnings


def _normalized_metric_score(value: float, threshold: float) -> float:
    if threshold <= 0.0:
        return 0.0
    return max(min(value / threshold, 1.25), 0.0) * 100.0


def _preferred_downside_scenario(cost_model: CostModel) -> ScenarioResult | None:
    non_base = [scenario for scenario in cost_model.scenario_results if scenario.scenario_name.lower() != "base"]
    if not non_base:
        return None
    explicit_conservative = next((scenario for scenario in non_base if scenario.scenario_name.lower() == "conservative"), None)
    if explicit_conservative is not None:
        return explicit_conservative
    return min(non_base, key=lambda item: item.gross_margin_inr)


def _scenario_financing_metrics(
    scenario: ScenarioResult,
    cost_model: CostModel,
    financing_basis: DecisionRecord,
) -> dict[str, float | list[str] | str]:
    interest_rate, debt_fraction = _financing_terms(financing_basis)
    _, idc_total = _construction_funding_terms(cost_model, interest_rate, debt_fraction)
    opening_debt = cost_model.total_capex * debt_fraction + idc_total
    debt_entries = _build_debt_entries(
        opening_debt,
        interest_rate,
        5,
        cost_model.citations + financing_basis.citations,
        cost_model.assumptions + financing_basis.assumptions,
    )
    if not debt_entries:
        return {
            "scenario_name": scenario.scenario_name,
            "minimum_dscr": 0.0,
            "average_dscr": 0.0,
            "llcr": 0.0,
            "plcr": 0.0,
            "breach_codes": [],
            "coverage_score": 0.0,
            "score": 0.0,
        }
    depreciation = cost_model.total_capex / 12.0
    average_interest = sum(entry.interest_inr for entry in debt_entries) / len(debt_entries)
    max_debt_service = max(entry.principal_repayment_inr + entry.interest_inr for entry in debt_entries)
    average_debt_service = sum(entry.principal_repayment_inr + entry.interest_inr for entry in debt_entries) / len(debt_entries)
    taxable_profit = max(scenario.annual_revenue_inr - scenario.annual_operating_cost_inr - depreciation - average_interest, 0.0)
    tax = taxable_profit * 0.25
    cfads = max(scenario.annual_revenue_inr - scenario.annual_operating_cost_inr - tax, 0.0)
    minimum_dscr = cfads / max(max_debt_service, 1.0)
    average_dscr = cfads / max(average_debt_service, 1.0)
    loan_life_cfads_pv = sum(cfads / ((1.0 + interest_rate) ** year) for year in range(1, len(debt_entries) + 1))
    project_life_cfads_pv = sum(cfads / ((1.0 + interest_rate) ** year) for year in range(1, 13))
    llcr = loan_life_cfads_pv / max(opening_debt, 1.0) if opening_debt > 0.0 else 0.0
    plcr = project_life_cfads_pv / max(opening_debt, 1.0) if opening_debt > 0.0 else 0.0
    breach_codes = _coverage_breach_codes(minimum_dscr, average_dscr, llcr, plcr, has_debt=opening_debt > 0.0)
    coverage_score = (
        0.35 * _normalized_metric_score(minimum_dscr, 1.10)
        + 0.15 * _normalized_metric_score(average_dscr, 1.25)
        + 0.25 * _normalized_metric_score(llcr if llcr > 0.0 else 1.30, 1.30)
        + 0.25 * _normalized_metric_score(plcr if plcr > 0.0 else 1.45, 1.45)
    )
    stability_score = max(100.0 - len(breach_codes) * 18.0, 20.0)
    downside_score = 0.85 * coverage_score + 0.15 * stability_score - max(len(breach_codes) - 1, 0) * 6.0
    return {
        "scenario_name": scenario.scenario_name,
        "minimum_dscr": round(minimum_dscr, 3),
        "average_dscr": round(average_dscr, 3),
        "llcr": round(llcr, 3),
        "plcr": round(plcr, 3),
        "breach_codes": breach_codes,
        "coverage_score": round(coverage_score, 3),
        "score": round(downside_score, 3),
    }


def _financing_option_total_score(
    base_score: float,
    financial_model: FinancialModel,
    financing_basis: DecisionRecord,
) -> tuple[float, dict[str, float]]:
    interest_rate, debt_fraction = _financing_terms(financing_basis)
    coverage_score = (
        0.35 * _normalized_metric_score(financial_model.minimum_dscr, 1.10)
        + 0.15 * _normalized_metric_score(financial_model.average_dscr, 1.25)
        + 0.25 * _normalized_metric_score(financial_model.llcr if financial_model.llcr > 0.0 else 1.30, 1.30)
        + 0.25 * _normalized_metric_score(financial_model.plcr if financial_model.plcr > 0.0 else 1.45, 1.45)
    )
    capital_cost_score = max(min((0.12 - interest_rate) / 0.015, 1.0), 0.0) * 100.0
    leverage_score = max(min((debt_fraction - 0.50) / 0.20, 1.0), 0.0) * 100.0
    return_score = _normalized_metric_score(financial_model.irr, 18.0)
    stability_score = max(100.0 - len(financial_model.covenant_breach_codes) * 18.0, 20.0)
    hard_penalty = 0.0
    if financial_model.minimum_dscr < 1.00:
        hard_penalty += 18.0
    if financial_model.llcr > 0.0 and financial_model.llcr < 1.15:
        hard_penalty += 14.0
    if financial_model.plcr > 0.0 and financial_model.plcr < 1.30:
        hard_penalty += 14.0
    total_score = (
        0.50 * coverage_score
        + 0.15 * capital_cost_score
        + 0.10 * leverage_score
        + 0.10 * return_score
        + 0.15 * base_score
        - hard_penalty
        - max(len(financial_model.covenant_breach_codes) - 1, 0) * 4.0
    )
    return round(total_score, 3), {
        "coverage": round(coverage_score, 3),
        "capital_cost": round(capital_cost_score, 3),
        "leverage": round(leverage_score, 3),
        "returns": round(return_score, 3),
        "base_preference": round(base_score, 3),
        "stability": round(stability_score, 3),
        "hard_penalty": round(hard_penalty, 3),
    }


def _construction_funding_terms(
    cost_model: CostModel,
    interest_rate: float,
    debt_fraction: float,
) -> tuple[list[dict[str, float | str]], float]:
    schedule_rows: list[dict[str, float | str]] = []
    idc_total = 0.0
    construction_months = max(cost_model.construction_months, 1)
    for row in cost_model.procurement_schedule:
        capex_draw = float(row.get("capex_draw_inr", 0.0))
        month = float(row.get("month", 0.0))
        debt_draw = capex_draw * debt_fraction
        equity_draw = capex_draw * (1.0 - debt_fraction)
        remaining_months = max(construction_months - month, 0.5)
        idc = debt_draw * interest_rate * (remaining_months / 12.0) * 0.55
        idc_total += idc
        schedule_rows.append(
            {
                "milestone": str(row.get("milestone", "")),
                "month": round(month, 1),
                "draw_fraction": round(float(row.get("draw_fraction", 0.0)), 6),
                "capex_draw_inr": round(capex_draw, 2),
                "debt_draw_inr": round(debt_draw, 2),
                "equity_draw_inr": round(equity_draw, 2),
                "idc_inr": round(idc, 2),
            }
        )
    return schedule_rows, round(idc_total, 2)


def _working_capital_timing_terms(
    cost_model: CostModel,
    operations_planning: OperationsPlanningArtifact | None,
) -> dict[str, float]:
    schedule = sorted(cost_model.procurement_schedule, key=lambda row: float(row.get("month", 0.0)))
    commissioning_reference_month = 0.90 * max(cost_model.construction_months, 1)
    if schedule:
        non_retention_rows = [row for row in schedule if str(row.get("milestone", "")) != "performance_retention"]
        reference_row = max(non_retention_rows or schedule, key=lambda row: float(row.get("month", 0.0)))
        commissioning_reference_month = float(reference_row.get("month", 0.0))
    startup_ramp_days = operations_planning.startup_ramp_days if operations_planning else 6.0
    raw_material_buffer_days = operations_planning.raw_material_buffer_days if operations_planning else 18.0
    restart_buffer_days = operations_planning.restart_buffer_days if operations_planning else 5.0
    procurement_timing_factor = min(
        1.0
        + 0.55 * cost_model.imported_equipment_fraction
        + 0.45 * cost_model.long_lead_equipment_fraction
        + max(cost_model.construction_months - 18, 0) / 18.0 * 0.10,
        1.85,
    )
    precommissioning_inventory_days = max(
        startup_ramp_days
        + 0.45 * raw_material_buffer_days
        + 0.25 * restart_buffer_days,
        8.0,
    ) * procurement_timing_factor
    payables_realization_fraction = max(0.35, 0.70 - 0.30 * (procurement_timing_factor - 1.0))
    precommissioning_inventory_month = min(
        commissioning_reference_month + max(startup_ramp_days / 60.0, 0.25),
        max(cost_model.construction_months, 1) + 1.5,
    )
    peak_working_capital_month = min(
        precommissioning_inventory_month + max(startup_ramp_days / 90.0, 0.20),
        max(cost_model.construction_months, 1) + 2.0,
    )
    return {
        "procurement_timing_factor": procurement_timing_factor,
        "precommissioning_inventory_days": precommissioning_inventory_days,
        "precommissioning_inventory_month": precommissioning_inventory_month,
        "peak_working_capital_month": peak_working_capital_month,
        "payables_realization_fraction": payables_realization_fraction,
    }


def _build_debt_entries(opening_debt: float, interest_rate: float, years: int, citations: list[str], assumptions: list[str]) -> list[DebtScheduleEntry]:
    entries: list[DebtScheduleEntry] = []
    if years <= 0:
        return entries
    principal_base = opening_debt / max(years, 1)
    balance = opening_debt
    for year in range(1, years + 1):
        principal = min(principal_base, balance)
        interest = balance * interest_rate
        closing = max(balance - principal, 0.0)
        entries.append(
            DebtScheduleEntry(
                year=year,
                opening_debt_inr=round(balance, 2),
                principal_repayment_inr=round(principal, 2),
                interest_inr=round(interest, 2),
                closing_debt_inr=round(closing, 2),
                citations=citations,
                assumptions=assumptions,
            )
        )
        balance = closing
    return entries


def _decision(decision_id: str, context: str, alternatives: list[AlternativeOption], citations: list[str], assumptions: list[str]) -> DecisionRecord:
    selected = max(alternatives, key=lambda item: item.total_score)
    approval_required = any(item.candidate_id != selected.candidate_id and abs(item.total_score - selected.total_score) <= 4.0 for item in alternatives)
    return DecisionRecord(
        decision_id=decision_id,
        context=context,
        criteria=[
            DecisionCriterion(name="India fit", weight=0.30, justification="Economic basis must fit India public data constraints."),
            DecisionCriterion(name="Cost competitiveness", weight=0.35, justification="Basis must remain competitive under public-data assumptions."),
            DecisionCriterion(name="Execution realism", weight=0.20, justification="Procurement and finance assumptions should be buildable."),
            DecisionCriterion(name="Scenario stability", weight=0.15, justification="Weak options should be surfaced for approval."),
        ],
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=f"{selected.description} selected as the current economic basis.",
        hard_constraint_results=["India-only site, tariff, labor, logistics, and regulatory basis enforced."],
        confidence=0.83 if not approval_required else 0.72,
        scenario_stability=ScenarioStability.BORDERLINE if approval_required else ScenarioStability.STABLE,
        approval_required=approval_required,
        citations=citations,
        assumptions=assumptions,
    )


def _utility_package_cost_terms(package_item) -> tuple[float, float]:
    role = package_item.package_role
    if role == "exchanger":
        base_cost = max(2_250_000.0, package_item.duty_kw * 3150.0)
        install_factor = 2.20 if "htm" in package_item.equipment_type.lower() else 2.05
    elif role == "circulation":
        base_cost = 1_600_000.0 + package_item.power_kw * 185000.0
        install_factor = 1.85
    elif role == "expansion":
        base_cost = 1_250_000.0 + package_item.volume_m3 * 780000.0
        install_factor = 2.00
    elif role == "relief":
        base_cost = 950_000.0 + package_item.volume_m3 * 620000.0
        install_factor = 1.75
    elif role == "header":
        base_cost = 1_150_000.0 + package_item.flow_m3_hr * 42000.0 + package_item.duty_kw * 180.0
        install_factor = 1.90
    else:
        base_cost = 650_000.0 + max(package_item.design_pressure_bar, 1.0) * 85000.0
        install_factor = 1.60
    return base_cost, install_factor


def _utility_island_sensitivity_weights(
    topology: str,
    package_items: list,
    cross_service: bool,
    direct_match_count: int,
    indirect_match_count: int,
) -> tuple[float, float, float]:
    topology_lower = topology.lower()
    circulation_count = sum(1 for item in package_items if item.package_role == "circulation")
    phase_change_count = sum(1 for item in package_items if item.phase_change_load_kg_hr > 0.0)
    htm_like = "htm" in topology_lower or any("htm" in item.equipment_type.lower() for item in package_items)
    direct_fraction = direct_match_count / max(direct_match_count + indirect_match_count, 1)
    steam_weight = 0.20 + (0.20 if htm_like else 0.08) + min(phase_change_count, 2) * 0.07 + max(0.45 - direct_fraction, 0.0) * 0.20
    power_weight = 0.22 + min(circulation_count, 2) * 0.10 + (0.08 if cross_service else 0.0) + (0.05 if "hybrid" in topology_lower else 0.0)
    capex_weight = max(0.18, 1.0 - steam_weight - power_weight)
    total = steam_weight + power_weight + capex_weight
    return steam_weight / total, power_weight / total, capex_weight / total


def _utility_island_maintenance_terms(island, package_items: list) -> tuple[float, float, float]:
    base_cycle_years = 4.8
    if island.architecture_role == "shared_htm":
        base_cycle_years += 0.8
    elif island.architecture_role == "condenser_reboiler_cluster":
        base_cycle_years -= 0.4
    elif island.architecture_role == "staged_header":
        base_cycle_years -= 0.2
    severity = (
        1.0
        + min(island.header_design_pressure_bar / 15.0, 1.2) * 0.14
        + min(island.control_complexity_factor / 4.0, 1.0) * 0.18
        + min(island.shared_htm_inventory_m3 / 6.0, 1.5) * 0.10
        + min(island.condenser_reboiler_pair_score / 20.0, 1.0) * 0.08
    )
    maintenance_cycle_years = max(base_cycle_years / max(severity, 0.7), 2.0)
    installed_cost = sum(
        _utility_package_cost_terms(package_item)[0] * _utility_package_cost_terms(package_item)[1]
        for package_item in package_items
    )
    replacement_fraction = (
        0.11
        + (0.03 if island.architecture_role == "shared_htm" else 0.0)
        + (0.02 if island.architecture_role == "staged_header" else 0.0)
    )
    replacement_event_cost = installed_cost * replacement_fraction
    planned_turnaround_days = (
        1.2
        + min(island.shared_htm_inventory_m3 / 8.0, 1.8)
        + min(island.control_complexity_factor, 3.0) * 0.35
        + (1.5 if island.architecture_role == "condenser_reboiler_cluster" else 0.0)
    )
    return maintenance_cycle_years, replacement_event_cost, planned_turnaround_days


def _utility_package_service_cost(base_cost: float, package_item, topology: str, cross_service: bool) -> float:
    role_fraction = {
        "exchanger": 0.012,
        "circulation": 0.021,
        "expansion": 0.009,
        "relief": 0.007,
        "controls": 0.015,
        "header": 0.010,
    }.get(package_item.package_role, 0.010)
    topology_lower = topology.lower()
    severity = 1.0
    if cross_service:
        severity += 0.08
    if "htm" in topology_lower:
        severity += 0.07
    if "hybrid" in topology_lower:
        severity += 0.04
    severity += min(package_item.power_kw / 250.0, 1.5) * 0.07
    severity += min(package_item.duty_kw / 25000.0, 1.5) * 0.05
    severity += min(package_item.phase_change_load_kg_hr / 10000.0, 1.5) * 0.05
    return base_cost * role_fraction * severity


def _build_utility_island_costs(
    utility_architecture: UtilityArchitectureDecision | None,
    utility_cost: float,
    annual_hours: float,
    total_capex: float,
    installed_cost: float,
    citations: list[str],
    assumptions: list[str],
) -> tuple[list[UtilityIslandEconomicImpact], float, float]:
    if utility_architecture is None:
        return [], 0.0, 0.0
    architecture = utility_architecture.architecture
    case_index = {case.case_id: case for case in architecture.cases}
    selected_case = case_index.get(architecture.selected_case_id or "")
    if selected_case is None or not selected_case.utility_islands:
        return [], 0.0, 0.0
    package_items_by_island: dict[str, list] = {}
    for package_item in architecture.selected_package_items:
        if package_item.island_id:
            package_items_by_island.setdefault(package_item.island_id, []).append(package_item)
    total_recovered = sum(max(island.recovered_duty_kw, 0.0) for island in selected_case.utility_islands)
    total_target = sum(max(island.target_recovered_duty_kw, 0.0) for island in selected_case.utility_islands)
    total_package_power = sum(
        sum(max(item.power_kw, 0.0) for item in package_items_by_island.get(island.island_id, []))
        for island in selected_case.utility_islands
    )
    utility_share_scores: dict[str, float] = {}
    island_rows: list[dict[str, float | str | list | bool]] = []
    for island in selected_case.utility_islands:
        package_items = package_items_by_island.get(island.island_id, [])
        bare_cost = 0.0
        installed = 0.0
        annual_service_cost = 0.0
        package_power = 0.0
        for package_item in package_items:
            base_cost, install_factor = _utility_package_cost_terms(package_item)
            bare_cost += base_cost
            installed += base_cost * install_factor
            annual_service_cost += _utility_package_service_cost(
                base_cost,
                package_item,
                island.topology,
                island.cross_service,
            )
            package_power += max(package_item.power_kw, 0.0)
        recovered_share = island.recovered_duty_kw / max(total_recovered, 1.0)
        target_share = island.target_recovered_duty_kw / max(total_target, 1.0)
        power_share = package_power / max(total_package_power, 1.0) if total_package_power > 0.0 else 0.0
        utility_share_score = 0.55 * recovered_share + 0.25 * target_share + 0.20 * power_share
        utility_share_scores[island.island_id] = utility_share_score
        steam_weight, power_weight, capex_weight = _utility_island_sensitivity_weights(
            island.topology,
            package_items,
            island.cross_service,
            island.direct_match_count,
            island.indirect_match_count,
        )
        maintenance_cycle_years, replacement_event_cost, planned_turnaround_days = _utility_island_maintenance_terms(
            island,
            package_items,
        )
        annualized_replacement_cost = replacement_event_cost / max(maintenance_cycle_years, 1.0)
        island_rows.append(
            {
                "island_id": island.island_id,
                "topology": island.topology,
                "package_items": package_items,
                "bare_cost": bare_cost,
                "installed_cost": installed,
                "annual_service_cost": annual_service_cost,
                "package_power": package_power,
                "recovered_share": recovered_share,
                "steam_weight": steam_weight,
                "power_weight": power_weight,
                "capex_weight": capex_weight,
                "maintenance_cycle_years": maintenance_cycle_years,
                "replacement_event_cost": replacement_event_cost,
                "annualized_replacement_cost": annualized_replacement_cost,
                "planned_turnaround_days": planned_turnaround_days,
                "cross_service": island.cross_service,
                "notes": (
                    f"Island cost burden derived from {len(package_items)} package items, "
                    f"{island.recovered_duty_kw:.1f} kW recovered duty, topology '{island.topology}', "
                    f"cycle {maintenance_cycle_years:.2f} y, turnaround {planned_turnaround_days:.2f} d."
                ),
            }
        )
    total_share_score = sum(utility_share_scores.values())
    island_costs: list[UtilityIslandEconomicImpact] = []
    annual_island_service_cost = 0.0
    annual_island_replacement_cost = 0.0
    for island in selected_case.utility_islands:
        row = next(item for item in island_rows if item["island_id"] == island.island_id)
        utility_share_fraction = (
            utility_share_scores[island.island_id] / total_share_score
            if total_share_score > 0.0
            else 1.0 / max(len(selected_case.utility_islands), 1)
        )
        installed_fraction = float(row["installed_cost"]) / max(installed_cost, 1.0)
        allocated_utility_cost = utility_cost * utility_share_fraction
        service_cost = float(row["annual_service_cost"])
        annualized_replacement_cost = float(row["annualized_replacement_cost"])
        annual_island_service_cost += service_cost
        annual_island_replacement_cost += annualized_replacement_cost
        island_costs.append(
            UtilityIslandEconomicImpact(
                island_id=island.island_id,
                topology=island.topology,
                train_step_count=len(island.train_step_ids),
                package_item_count=len(row["package_items"]),
                shared_htm_inventory_m3=island.shared_htm_inventory_m3,
                header_design_pressure_bar=island.header_design_pressure_bar,
                condenser_reboiler_pair_score=island.condenser_reboiler_pair_score,
                control_complexity_factor=island.control_complexity_factor,
                recovered_duty_kw=island.recovered_duty_kw,
                recovered_duty_share_fraction=round(float(row["recovered_share"]), 6),
                utility_cost_share_fraction=round(utility_share_fraction, 6),
                capex_share_fraction=round(installed_fraction, 6),
                bare_cost_inr=round(float(row["bare_cost"]), 2),
                installed_cost_inr=round(float(row["installed_cost"]), 2),
                project_capex_burden_inr=round(total_capex * installed_fraction, 2),
                annual_allocated_utility_cost_inr=round(allocated_utility_cost, 2),
                annual_service_cost_inr=round(service_cost, 2),
                annualized_replacement_cost_inr=round(annualized_replacement_cost, 2),
                annual_operating_burden_inr=round(allocated_utility_cost + service_cost + annualized_replacement_cost, 2),
                maintenance_cycle_years=round(float(row["maintenance_cycle_years"]), 3),
                replacement_event_cost_inr=round(float(row["replacement_event_cost"]), 2),
                planned_turnaround_days=round(float(row["planned_turnaround_days"]), 3),
                steam_sensitivity_weight=round(float(row["steam_weight"]), 6),
                power_sensitivity_weight=round(float(row["power_weight"]), 6),
                capex_sensitivity_weight=round(float(row["capex_weight"]), 6),
                notes=str(row["notes"]),
                citations=sorted(set(citations + island.citations)),
                assumptions=sorted(set(assumptions + island.assumptions)),
            )
        )
    return island_costs, round(annual_island_service_cost, 2), round(annual_island_replacement_cost, 2)


def _utility_train_cost_items(
    utility_architecture: UtilityArchitectureDecision | None,
    procurement_profile: dict[str, float | int | str | list[dict[str, float | str]]],
    citations: list[str],
    assumptions: list[str],
) -> tuple[list[EquipmentCostItem], float]:
    if utility_architecture is None or not utility_architecture.architecture.selected_package_items:
        return [], 0.0
    items: list[EquipmentCostItem] = []
    installed_total = 0.0
    for package_item in utility_architecture.architecture.selected_package_items:
        base_cost, install_factor = _utility_package_cost_terms(package_item)
        procurement_terms = _procurement_package_terms(package_item.equipment_type, package_item.service, procurement_profile)
        import_duty = (
            base_cost
            * float(procurement_terms["import_content_fraction"])
            * float(procurement_terms["import_duty_fraction"])
        )
        bare_cost = base_cost + import_duty
        installed_cost = base_cost * install_factor
        installed_cost = bare_cost * install_factor
        installed_total += installed_cost
        items.append(
            EquipmentCostItem(
                equipment_id=package_item.equipment_id,
                equipment_type=package_item.equipment_type,
                service=package_item.service,
                basis=(
                    f"role={package_item.package_role}; duty={package_item.duty_kw:.3f} kW; "
                    f"power={package_item.power_kw:.3f} kW; volume={package_item.volume_m3:.3f} m3"
                ),
                bare_cost_inr=round(bare_cost, 2),
                installed_cost_inr=round(installed_cost, 2),
                spares_cost_inr=round(base_cost * 0.02, 2),
                procurement_package_family=str(procurement_terms["package_family"]),
                procurement_lead_time_months=round(float(procurement_terms["lead_time_months"]), 3),
                procurement_award_month=round(float(procurement_terms["award_month"]), 2),
                procurement_delivery_month=round(float(procurement_terms["delivery_month"]), 2),
                import_content_fraction=round(float(procurement_terms["import_content_fraction"]), 6),
                import_duty_fraction=round(float(procurement_terms["import_duty_fraction"]), 6),
                import_duty_inr=round(import_duty, 2),
                notes=(
                    "Utility-train package cost item derived from the selected package inventory. "
                    f"Procurement family {procurement_terms['package_family']} with import duty INR {import_duty:,.2f}."
                ),
                citations=sorted(set(citations + package_item.citations)),
                assumptions=sorted(set(assumptions + package_item.assumptions)),
            )
        )
    return items, round(installed_total, 2)


def build_procurement_basis_decision(
    site: SiteSelectionArtifact,
    equipment: list[EquipmentSpec],
    route_site_fit: RouteSiteFitArtifact | None = None,
    route_economic_basis: RouteEconomicBasisArtifact | None = None,
) -> DecisionRecord:
    coastal = "port" in " ".join(location.port_access.lower() for location in site.india_location_data)
    route_notes: list[str] = []
    domestic_score = 92.0 if coastal else 86.0
    mixed_score = 84.0 if coastal else 72.0
    import_score = 68.0 if coastal else 55.0
    if route_site_fit is not None:
        route_notes.append(
            f"route site-fit {route_site_fit.overall_fit_score:.1f} with blueprint "
            f"{route_site_fit.blueprint_step_count} steps / {route_site_fit.separation_duty_count} separation duties"
        )
        domestic_score -= max(route_site_fit.logistics_penalty_factor - 1.0, 0.0) * 120.0
        domestic_score -= max(route_site_fit.port_dependency_factor - 0.20, 0.0) * 45.0
        mixed_score += max(route_site_fit.port_dependency_factor - 0.18, 0.0) * 65.0
        import_score += route_site_fit.port_dependency_factor * (25.0 if coastal else 40.0)
        if route_site_fit.batch_capable:
            domestic_score += 4.0 if not coastal else 1.0
            mixed_score += 2.0
    if route_economic_basis is not None:
        route_notes.append(
            f"raw-material complexity {route_economic_basis.raw_material_complexity_factor:.3f}; "
            f"logistics intensity {route_economic_basis.logistics_intensity_factor:.3f}"
        )
        domestic_score -= max(route_economic_basis.raw_material_complexity_factor - 1.0, 0.0) * 30.0
        domestic_score -= max(route_economic_basis.logistics_intensity_factor - 1.0, 0.0) * 55.0
        mixed_score += max(route_economic_basis.logistics_intensity_factor - 1.0, 0.0) * 42.0
        import_score += max(route_economic_basis.logistics_intensity_factor - 1.0, 0.0) * 68.0
        if route_economic_basis.coverage_status == "grounded":
            domestic_score += 2.0
            mixed_score += 2.0
        elif route_economic_basis.coverage_status == "screening":
            import_score -= 3.0
    context = f"Procurement basis for {site.selected_site} and {len(equipment)} equipment items."
    if route_notes:
        context += " Route/blueprint context: " + "; ".join(route_notes) + "."
    options = [
        AlternativeOption(candidate_id="domestic_cluster_procurement", candidate_type="procurement_basis", description="Domestic cluster-led procurement", total_score=round(domestic_score, 3), feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="mixed_import_domestic", candidate_type="procurement_basis", description="Mixed import and domestic procurement", total_score=round(mixed_score, 3), feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="import_heavy", candidate_type="procurement_basis", description="Import-heavy procurement", total_score=round(import_score, 3), feasible=True, citations=site.citations, assumptions=site.assumptions),
    ]
    return _decision("procurement_basis", context, options, site.citations, site.assumptions)


def build_financing_basis_decision(basis: ProjectBasis, site: SiteSelectionArtifact) -> DecisionRecord:
    options = [
        AlternativeOption(candidate_id="debt_equity_70_30", candidate_type="financing_basis", description="70:30 debt-equity basis", total_score=90.0 if basis.capacity_tpa >= 100000 else 82.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="debt_equity_60_40", candidate_type="financing_basis", description="60:40 debt-equity basis", total_score=86.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="conservative_50_50", candidate_type="financing_basis", description="50:50 conservative financing basis", total_score=72.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
    ]
    return _decision("financing_basis", f"Financing basis for {basis.target_product} in India.", options, site.citations, site.assumptions)


def evaluate_financing_basis_decision(
    basis: ProjectBasis,
    market_price_per_kg: float,
    cost_model: CostModel,
    working_capital: WorkingCapitalModel,
    citations: list[str],
    assumptions: list[str],
    financing_basis_seed: DecisionRecord,
) -> tuple[DecisionRecord, FinancialModel]:
    evaluated_options: list[AlternativeOption] = []
    candidate_models: dict[str, FinancialModel] = {}
    downside_metrics_by_candidate: dict[str, dict[str, float | list[str] | str]] = {}
    downside_scenario = _preferred_downside_scenario(cost_model)
    for alternative in financing_basis_seed.alternatives:
        candidate_basis = financing_basis_seed.model_copy(
            update={
                "selected_candidate_id": alternative.candidate_id,
                "selected_summary": f"{alternative.description} under lender-coverage screening.",
                "approval_required": False,
                "scenario_stability": ScenarioStability.STABLE,
            },
            deep=True,
        )
        candidate_model = build_financial_model_v2(
            basis,
            market_price_per_kg,
            cost_model,
            working_capital,
            citations,
            assumptions,
            candidate_basis,
        )
        candidate_models[alternative.candidate_id] = candidate_model
        total_score, score_breakdown = _financing_option_total_score(
            alternative.total_score,
            candidate_model,
            candidate_basis,
        )
        downside_metrics = (
            _scenario_financing_metrics(downside_scenario, cost_model, candidate_basis)
            if downside_scenario is not None
            else {
                "scenario_name": "",
                "minimum_dscr": 0.0,
                "average_dscr": 0.0,
                "llcr": 0.0,
                "plcr": 0.0,
                "breach_codes": [],
                "coverage_score": 0.0,
                "score": total_score,
            }
        )
        downside_metrics_by_candidate[alternative.candidate_id] = downside_metrics
        combined_total_score = total_score
        if downside_scenario is not None:
            combined_total_score = round(0.55 * total_score + 0.45 * float(downside_metrics["score"]), 3)
        rejected_reasons = [
            {
                "minimum_dscr_breach": "Minimum DSCR is below the lender screening threshold.",
                "average_dscr_breach": "Average DSCR is below the lender screening threshold.",
                "llcr_breach": "LLCR is below the lender screening threshold.",
                "plcr_breach": "PLCR is below the lender screening threshold.",
            }[code]
            for code in candidate_model.covenant_breach_codes
        ]
        rejected_reasons.extend(
            {
                "minimum_dscr_breach": f"{downside_metrics['scenario_name']} scenario minimum DSCR is below the lender screening threshold.",
                "average_dscr_breach": f"{downside_metrics['scenario_name']} scenario average DSCR is below the lender screening threshold.",
                "llcr_breach": f"{downside_metrics['scenario_name']} scenario LLCR is below the lender screening threshold.",
                "plcr_breach": f"{downside_metrics['scenario_name']} scenario PLCR is below the lender screening threshold.",
            }[code]
            for code in downside_metrics["breach_codes"]
            if downside_metrics["scenario_name"]
        )
        deduped_reasons: list[str] = []
        for reason in rejected_reasons:
            if reason not in deduped_reasons:
                deduped_reasons.append(reason)
        interest_rate, debt_fraction = _financing_terms(candidate_basis)
        evaluated_options.append(
            alternative.model_copy(
                update={
                    "inputs": {
                        "interest_rate": f"{interest_rate:.4f}",
                        "debt_fraction": f"{debt_fraction:.3f}",
                    },
                    "outputs": {
                        "minimum_dscr": f"{candidate_model.minimum_dscr:.3f}",
                        "average_dscr": f"{candidate_model.average_dscr:.3f}",
                        "llcr": f"{candidate_model.llcr:.3f}",
                        "plcr": f"{candidate_model.plcr:.3f}",
                        "irr_pct": f"{candidate_model.irr:.2f}",
                        "npv_inr": f"{candidate_model.npv:.2f}",
                        "idc_inr": f"{candidate_model.construction_interest_during_construction_inr:.2f}",
                        "coverage_status": "warning" if candidate_model.covenant_breach_codes else "pass",
                        "downside_scenario_name": str(downside_metrics["scenario_name"]),
                        "downside_minimum_dscr": f"{float(downside_metrics['minimum_dscr']):.3f}",
                        "downside_average_dscr": f"{float(downside_metrics['average_dscr']):.3f}",
                        "downside_llcr": f"{float(downside_metrics['llcr']):.3f}",
                        "downside_plcr": f"{float(downside_metrics['plcr']):.3f}",
                        "downside_coverage_status": "warning" if downside_metrics["breach_codes"] else "pass",
                        "downside_breach_count": str(len(downside_metrics["breach_codes"])),
                    },
                    "rejected_reasons": deduped_reasons,
                    "score_breakdown": {
                        **score_breakdown,
                        "base_total": round(total_score, 3),
                        "downside_coverage": float(downside_metrics["coverage_score"]),
                        "downside_total": float(downside_metrics["score"]),
                    },
                    "total_score": combined_total_score,
                    "feasible": True,
                },
                deep=True,
            )
        )
    evaluated_options.sort(key=lambda item: item.total_score, reverse=True)
    base_preferred_option = max(evaluated_options, key=lambda item: item.score_breakdown.get("base_total", item.total_score))
    downside_preferred_option = max(evaluated_options, key=lambda item: item.score_breakdown.get("downside_total", item.total_score))
    selected_option = evaluated_options[0]
    selected_model = candidate_models[selected_option.candidate_id]
    scenario_reversal = downside_scenario is not None and selected_option.candidate_id != base_preferred_option.candidate_id
    if downside_scenario is not None and downside_preferred_option.candidate_id != selected_option.candidate_id:
        selected_downside_breaches = len(downside_metrics_by_candidate[selected_option.candidate_id]["breach_codes"])
        preferred_downside_breaches = len(downside_metrics_by_candidate[downside_preferred_option.candidate_id]["breach_codes"])
        downside_advantage = float(downside_preferred_option.score_breakdown.get("downside_total", 0.0)) - float(
            selected_option.score_breakdown.get("downside_total", 0.0)
        )
        if preferred_downside_breaches + 1 < selected_downside_breaches or downside_advantage > 12.0:
            selected_option = downside_preferred_option
            selected_model = candidate_models[selected_option.candidate_id]
            scenario_reversal = selected_option.candidate_id != base_preferred_option.candidate_id
    remaining_scores = [
        option.total_score
        for option in evaluated_options
        if option.candidate_id != selected_option.candidate_id
    ]
    runner_up_score = max(remaining_scores) if remaining_scores else 0.0
    selection_gap = selected_option.total_score - runner_up_score
    approval_required = bool(selected_model.covenant_breach_codes) or selection_gap <= 4.0 or scenario_reversal
    scenario_stability = ScenarioStability.STABLE
    if selected_model.covenant_breach_codes:
        scenario_stability = (
            ScenarioStability.UNSTABLE
            if any(code in {"minimum_dscr_breach", "llcr_breach", "plcr_breach"} for code in selected_model.covenant_breach_codes)
            else ScenarioStability.BORDERLINE
        )
    elif scenario_reversal or selection_gap <= 4.0:
        scenario_stability = ScenarioStability.BORDERLINE
    downgraded_options = [
        option.candidate_id
        for option in evaluated_options
        if option.candidate_id != selected_option.candidate_id and option.total_score > selected_option.total_score - 12.0 and option.rejected_reasons
    ]
    summary = (
        f"{selected_option.description} selected after lender-coverage reranking "
        f"(min DSCR {selected_model.minimum_dscr:.3f}, LLCR {selected_model.llcr:.3f}, PLCR {selected_model.plcr:.3f})."
    )
    if downgraded_options:
        summary += " Higher-leverage options were downgraded because of covenant pressure."
    if scenario_reversal and downside_scenario is not None:
        summary += (
            f" Downside scenario '{downside_scenario.scenario_name}' overturned the base financing preference "
            f"in favor of {selected_option.description}."
        )
    if selected_model.covenant_breach_codes:
        summary += " The selected basis still carries covenant pressure and requires approval."
    hard_constraints = [
        "Financing options were reranked against minimum DSCR 1.10, average DSCR 1.25, LLCR 1.30, and PLCR 1.45.",
    ]
    if downside_scenario is not None:
        hard_constraints.append(
            f"Downside financing ranking used scenario '{downside_scenario.scenario_name}' to test covenant resilience beyond the base case."
        )
    for option in evaluated_options:
        if option.rejected_reasons:
            hard_constraints.append(
                f"{option.candidate_id}: " + "; ".join(option.rejected_reasons)
            )
    reranked_decision = financing_basis_seed.model_copy(
        update={
            "alternatives": evaluated_options,
            "selected_candidate_id": selected_option.candidate_id,
            "selected_summary": summary,
            "hard_constraint_results": hard_constraints,
            "confidence": 0.84 if not approval_required else 0.68,
            "scenario_stability": scenario_stability,
            "approval_required": approval_required,
        },
        deep=True,
    )
    selected_model = selected_model.model_copy(
        update={
            "selected_financing_candidate_id": reranked_decision.selected_candidate_id or "",
            "selected_financing_description": selected_option.description,
            "downside_scenario_name": downside_scenario.scenario_name if downside_scenario is not None else "",
            "downside_financing_candidate_id": downside_preferred_option.candidate_id if downside_scenario is not None else "",
            "financing_scenario_reversal": scenario_reversal,
        },
        deep=True,
    )
    return reranked_decision, selected_model


def build_logistics_basis_decision(
    site: SiteSelectionArtifact,
    market: MarketAssessmentArtifact,
    route_site_fit: RouteSiteFitArtifact | None = None,
    route_economic_basis: RouteEconomicBasisArtifact | None = None,
) -> DecisionRecord:
    coastal = site.selected_site.lower() in {"dahej", "jamnagar", "paradip"}
    coastal_score = 92.0 if coastal else 70.0
    inland_score = 84.0 if not coastal else 78.0
    context = f"Logistics basis for {site.selected_site}."
    if route_site_fit is not None:
        coastal_score += route_site_fit.port_dependency_factor * (18.0 if coastal else 28.0)
        coastal_score -= max(route_site_fit.logistics_penalty_factor - 1.0, 0.0) * 90.0
        inland_score += (4.0 if route_site_fit.batch_capable and not coastal else 0.0)
        inland_score -= max(route_site_fit.port_dependency_factor - 0.15, 0.0) * 24.0
        context += (
            f" Route site-fit score {route_site_fit.overall_fit_score:.1f} with "
            f"port dependency {route_site_fit.port_dependency_factor:.3f}."
        )
    if route_economic_basis is not None:
        coastal_score += max(route_economic_basis.logistics_intensity_factor - 1.0, 0.0) * (40.0 if coastal else 18.0)
        inland_score -= max(route_economic_basis.logistics_intensity_factor - 1.0, 0.0) * 36.0
        inland_score += route_economic_basis.batch_occupancy_penalty_fraction * (18.0 if not coastal else 8.0)
        context += (
            f" Blueprint-driven logistics intensity {route_economic_basis.logistics_intensity_factor:.3f} "
            f"and batch penalty {route_economic_basis.batch_occupancy_penalty_fraction:.3f} were applied."
        )
    options = [
        AlternativeOption(candidate_id="coastal_cluster_dispatch", candidate_type="logistics_basis", description="Coastal cluster dispatch basis", total_score=round(coastal_score, 3), feasible=True, citations=site.citations + market.citations, assumptions=site.assumptions + market.assumptions),
        AlternativeOption(candidate_id="rail_road_inland", candidate_type="logistics_basis", description="Rail-road inland dispatch basis", total_score=round(inland_score, 3), feasible=True, citations=site.citations + market.citations, assumptions=site.assumptions + market.assumptions),
    ]
    return _decision("logistics_basis", context, options, site.citations + market.citations, site.assumptions + market.assumptions)


def build_cost_model_v2(
    basis: ProjectBasis,
    equipment: list[EquipmentSpec],
    utilities: UtilitySummaryArtifact,
    stream_table: StreamTable,
    market: MarketAssessmentArtifact,
    site: SiteSelectionArtifact,
    scenario_policy: ScenarioPolicy,
    citations: list[str],
    assumptions: list[str],
    procurement_basis: DecisionRecord,
    logistics_basis: DecisionRecord,
    route_site_fit: RouteSiteFitArtifact | None = None,
    route_economic_basis: RouteEconomicBasisArtifact | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
    column_design: ColumnDesign | None = None,
) -> CostModel:
    price_data = list(market.india_price_data)
    if not price_data:
        price_data = [
            IndianPriceDatum(datum_id="product", category="product", item_name=basis.target_product, region=site.selected_site, units="INR/kg", value_inr=market.estimated_price_per_kg, reference_year=basis.economic_reference_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="power", category="utility", item_name="Electricity", region=site.selected_site, units="INR/kWh", value_inr=8.5, reference_year=basis.utility_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="steam", category="utility", item_name="Steam", region=site.selected_site, units="INR/kg", value_inr=1.8, reference_year=basis.utility_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="cooling_water", category="utility", item_name="Cooling water", region=site.selected_site, units="INR/m3", value_inr=utilities.utility_basis.cooling_water_cost_inr_per_m3 if utilities.utility_basis else 8.0, reference_year=basis.utility_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
            IndianPriceDatum(datum_id="labor", category="labor", item_name="Operating labour", region=site.selected_site, units="INR/person-year", value_inr=650000.0, reference_year=basis.labor_basis_year, normalization_year=basis.economic_reference_year, citations=citations),
        ]
    annual_hours = _operating_hours(basis)
    purchase_cost = 0.0
    equipment_cost_items: list[EquipmentCostItem] = []
    absorber_transport_service_cost = 0.0
    solids_transport_service_cost = 0.0
    annual_packing_replacement_cost = 0.0
    annual_classifier_service_cost = 0.0
    annual_filter_media_replacement_cost = 0.0
    annual_dryer_exhaust_treatment_cost = 0.0
    annual_utility_island_service_cost = 0.0
    annual_utility_island_replacement_cost = 0.0
    packing_replacement_cycle_years = 0.0
    packing_replacement_event_cost = 0.0
    availability_policy = _availability_policy_for_cost_model(column_design)
    procurement_profile = _procurement_profile_for_cost_model(procurement_basis, equipment)
    utility_package_ids = {
        package_item.equipment_id
        for package_item in (utility_architecture.architecture.selected_package_items if utility_architecture is not None else [])
    }
    for item in equipment:
        if item.equipment_id in utility_package_ids:
            continue
        equipment_factor = {
            "reactor": 700000.0,
            "process unit": 280000.0,
            "distillation column": 340000.0,
            "absorber": 310000.0,
            "packing internals": 265000.0,
            "crystallizer train": 295000.0,
            "crystal classifier": 245000.0,
            "pressure filter": 360000.0,
            "dryer gas handling skid": 285000.0,
            "extraction column": 300000.0,
            "flash drum": 190000.0,
            "heat exchanger": 420000.0,
            "storage tank": 120000.0,
            "htm circulation skid": 280000.0,
            "htm expansion tank": 160000.0,
            "htm relief package": 140000.0,
            "utility control package": 90000.0,
        }.get(item.equipment_type.lower(), 220000.0)
        (
            capex_multiplier,
            installed_multiplier,
            spares_fraction,
            note_lines,
            service_cost_basis,
        ) = _equipment_cost_terms(item, column_design)
        procurement_terms = _procurement_package_terms(item.equipment_type, item.service, procurement_profile)
        base_bare_cost = max(2_500_000.0, (item.volume_m3 * equipment_factor + item.duty_kw * 1800.0) * capex_multiplier)
        import_duty = (
            base_bare_cost
            * float(procurement_terms["import_content_fraction"])
            * float(procurement_terms["import_duty_fraction"])
        )
        bare_cost = base_bare_cost + import_duty
        installed_item_cost = bare_cost * installed_multiplier
        spares_cost = base_bare_cost * spares_fraction
        if item.equipment_type.lower() == "packing internals":
            structured = bool(column_design and column_design.absorber_packing_family.startswith("structured"))
            replacement_fraction = 0.42 if structured else 0.30
            packing_severity = (
                1.0
                + (max(column_design.absorber_total_pressure_drop_kpa, 0.0) / 18.0 if column_design is not None else 0.0) * 0.18
                + (max(1.0 - column_design.absorber_wetting_ratio, 0.0) if column_design is not None else 0.0) * 0.25
                + (max(0.18 - column_design.absorber_flooding_margin_fraction, 0.0) if column_design is not None else 0.0) * 0.90
            )
            replacement_cycle_years = max((6.0 if structured else 4.5) / max(packing_severity, 0.6), 2.2)
            replacement_event_cost = bare_cost * replacement_fraction
            annual_packing_replacement_cost += replacement_event_cost / replacement_cycle_years
            absorber_transport_service_cost += replacement_event_cost / replacement_cycle_years
            packing_replacement_cycle_years = max(packing_replacement_cycle_years, replacement_cycle_years)
            packing_replacement_event_cost += replacement_event_cost
            note_lines.append(
                f"Packing replacement cycle {replacement_cycle_years:.2f} y with replacement fraction {replacement_fraction:.2f} under severity {packing_severity:.3f}."
            )
        elif item.equipment_type.lower() == "crystal classifier":
            annual_classifier_service_cost += service_cost_basis * annual_hours
            solids_transport_service_cost += service_cost_basis * annual_hours
            note_lines.append(
                f"Classifier recurring service cost annualized from slurry-handling severity: INR {service_cost_basis * annual_hours:,.2f}/y."
            )
        elif item.equipment_type.lower() in {"pressure filter", "dryer gas handling skid"}:
            if item.equipment_type.lower() == "pressure filter":
                annual_filter_media_replacement_cost += service_cost_basis
                note_lines.append(
                    f"Filter media replacement basis contributes INR {service_cost_basis:,.2f}/y."
                )
            else:
                annual_dryer_exhaust_treatment_cost += service_cost_basis
                note_lines.append(
                    f"Dryer exhaust treatment basis contributes INR {service_cost_basis:,.2f}/y."
                )
            solids_transport_service_cost += service_cost_basis
        note_lines.append(
            f"Procurement family {procurement_terms['package_family']} with lead time {float(procurement_terms['lead_time_months']):.2f} months "
            f"and import-duty burden INR {import_duty:,.2f}."
        )
        purchase_cost += bare_cost
        equipment_cost_items.append(
            EquipmentCostItem(
                equipment_id=item.equipment_id,
                equipment_type=item.equipment_type,
                service=item.service,
                basis=item.design_basis,
                bare_cost_inr=round(bare_cost, 2),
                installed_cost_inr=round(installed_item_cost, 2),
                spares_cost_inr=round(spares_cost, 2),
                procurement_package_family=str(procurement_terms["package_family"]),
                procurement_lead_time_months=round(float(procurement_terms["lead_time_months"]), 3),
                procurement_award_month=round(float(procurement_terms["award_month"]), 2),
                procurement_delivery_month=round(float(procurement_terms["delivery_month"]), 2),
                import_content_fraction=round(float(procurement_terms["import_content_fraction"]), 6),
                import_duty_fraction=round(float(procurement_terms["import_duty_fraction"]), 6),
                import_duty_inr=round(import_duty, 2),
                notes=" ".join(
                    [
                        f"Screening equipment cost derived from volume={item.volume_m3:.3f} m3 and duty={item.duty_kw:.3f} kW."
                    ]
                    + note_lines
                ).strip(),
                citations=item.citations,
                assumptions=item.assumptions,
            )
        )
    utility_train_items, utility_train_installed_capex = _utility_train_cost_items(utility_architecture, procurement_profile, citations, assumptions)
    if utility_train_items:
        equipment_cost_items.extend(utility_train_items)
        purchase_cost += sum(item.bare_cost_inr for item in utility_train_items)
    route_feedstock_cluster_factor = route_site_fit.feedstock_cluster_factor if route_site_fit is not None else 1.0
    route_logistics_penalty_factor = route_site_fit.logistics_penalty_factor if route_site_fit is not None else 1.0
    route_batch_penalty_fraction = route_economic_basis.batch_occupancy_penalty_fraction if route_economic_basis is not None else 0.0
    route_solvent_recovery_service_cost = route_economic_basis.solvent_recovery_service_cost_inr if route_economic_basis is not None else 0.0
    route_catalyst_service_cost = route_economic_basis.catalyst_service_cost_inr if route_economic_basis is not None else 0.0
    route_waste_treatment_burden = route_economic_basis.waste_treatment_burden_inr if route_economic_basis is not None else 0.0
    raw_material_complexity_factor = route_economic_basis.raw_material_complexity_factor if route_economic_basis is not None else 1.0
    site_input_cost_factor = route_economic_basis.site_input_cost_factor if route_economic_basis is not None else 1.0
    logistics_intensity_factor = route_economic_basis.logistics_intensity_factor if route_economic_basis is not None else 1.0
    installed_factor = 2.15 if procurement_basis.selected_candidate_id == "domestic_cluster_procurement" else 2.35
    installed_factor *= 1.0 + 0.015 * max(raw_material_complexity_factor - 1.0, 0.0)
    logistics_penalty = 0.02 if logistics_basis.selected_candidate_id == "coastal_cluster_dispatch" else 0.06
    logistics_penalty *= route_logistics_penalty_factor * (0.98 + 0.06 * max(logistics_intensity_factor - 1.0, 0.0))
    installed_cost = purchase_cost * installed_factor
    direct_cost = installed_cost * (1.14 + logistics_penalty)
    indirect_cost = direct_cost * 0.24
    contingency = direct_cost * 0.10
    total_capex = direct_cost + indirect_cost + contingency
    procurement_package_impacts, procurement_schedule, total_import_duty = _build_procurement_package_impacts(
        equipment_cost_items,
        procurement_profile,
        total_capex,
        citations,
        assumptions,
    )
    feed_mass = _fresh_makeup_mass_kg_hr(stream_table) * annual_hours
    if feed_mass <= 0.0:
        feed_mass = sum(
            component.mass_flow_kg_hr
            for stream in stream_table.streams
            if stream.stream_role == "feed"
            for component in stream.components
        ) * annual_hours
    if feed_mass <= 0.0:
        feed_mass = sum(
            component.mass_flow_kg_hr
            for stream in stream_table.streams
            if stream.stream_id.startswith("S-10")
            for component in stream.components
        ) * annual_hours
    benchmark_raw_material_price = market.estimated_price_per_kg * 0.58
    raw_material_cost = feed_mass * benchmark_raw_material_price * raw_material_complexity_factor * site_input_cost_factor
    utility_price_power = (
        utilities.utility_basis.power_cost_inr_per_kwh
        if utilities.utility_basis is not None
        else _find_price(price_data, "Electricity", 8.5)
    )
    utility_price_steam = (
        utilities.utility_basis.steam_cost_inr_per_kg
        if utilities.utility_basis is not None
        else _find_price(price_data, "Steam", 1.8)
    )
    utility_price_cw = (
        utilities.utility_basis.cooling_water_cost_inr_per_m3
        if utilities.utility_basis is not None
        else _find_price(price_data, "Cooling water", 8.0)
    )
    steam_load = _sum_utility_load(utilities, "Steam")
    power_load = _sum_utility_load(utilities, "Electricity")
    cw_load = _sum_utility_load(utilities, "Cooling water")
    utility_cost = steam_load * annual_hours * utility_price_steam + power_load * annual_hours * utility_price_power + cw_load * annual_hours * utility_price_cw
    utility_island_costs, annual_utility_island_service_cost, annual_utility_island_replacement_cost = _build_utility_island_costs(
        utility_architecture,
        utility_cost,
        annual_hours,
        total_capex,
        installed_cost,
        citations,
        assumptions,
    )
    labor_cost = 240.0 * _find_price(price_data, "Operating labour", 650000.0) * (1.0 + route_batch_penalty_fraction * 0.40)
    transport_service_cost = (
        annual_packing_replacement_cost
        + annual_classifier_service_cost
        + annual_filter_media_replacement_cost
        + annual_dryer_exhaust_treatment_cost
        + annual_utility_island_service_cost
        + annual_utility_island_replacement_cost
        + route_solvent_recovery_service_cost
        + route_catalyst_service_cost
        + route_waste_treatment_burden
    )
    maintenance_turnaround_cycle_years = int(availability_policy["turnaround_cycle_years"])
    maintenance_turnaround_event_cost = (
        max(total_capex * float(availability_policy["turnaround_event_fraction"]), 0.0)
        + max(cost_model_item.installed_cost_inr for cost_model_item in equipment_cost_items) * 0.010
        if equipment_cost_items
        else max(total_capex * float(availability_policy["turnaround_event_fraction"]), 0.0)
    )
    maintenance_cost = total_capex * 0.028 + transport_service_cost
    overheads = 0.19 * (labor_cost + maintenance_cost)
    annual_opex = raw_material_cost + utility_cost + labor_cost + maintenance_cost + overheads
    non_island_capex = max(total_capex - sum(item.project_capex_burden_inr for item in utility_island_costs), 0.0)
    non_island_utility_cost = max(utility_cost - sum(item.annual_allocated_utility_cost_inr for item in utility_island_costs), 0.0)
    scenario_results: list[ScenarioResult] = []
    for scenario in scenario_policy.cases:
        island_scenario_impacts: list[UtilityIslandScenarioImpact] = []
        scenario_island_utility = 0.0
        scenario_island_service = 0.0
        scenario_island_replacement = 0.0
        scenario_island_capex = 0.0
        for island_cost in utility_island_costs:
            utility_multiplier = (
                island_cost.steam_sensitivity_weight * scenario.steam_price_multiplier
                + island_cost.power_sensitivity_weight * scenario.power_price_multiplier
                + island_cost.capex_sensitivity_weight * (0.55 * scenario.steam_price_multiplier + 0.45 * scenario.power_price_multiplier)
            )
            service_multiplier = (
                0.70 * island_cost.capex_sensitivity_weight * scenario.capex_multiplier
                + 0.20 * island_cost.power_sensitivity_weight * scenario.power_price_multiplier
                + 0.10 * island_cost.steam_sensitivity_weight * scenario.steam_price_multiplier
            )
            capex_multiplier = (
                0.82 * scenario.capex_multiplier
                + 0.10 * island_cost.power_sensitivity_weight * scenario.power_price_multiplier
                + 0.08 * island_cost.steam_sensitivity_weight * scenario.steam_price_multiplier
            )
            island_utility = island_cost.annual_allocated_utility_cost_inr * utility_multiplier
            island_service = island_cost.annual_service_cost_inr * service_multiplier
            island_replacement = island_cost.annualized_replacement_cost_inr * (
                0.82 * scenario.capex_multiplier
                + 0.10 * island_cost.power_sensitivity_weight * scenario.power_price_multiplier
                + 0.08 * island_cost.steam_sensitivity_weight * scenario.steam_price_multiplier
            )
            island_capex = island_cost.project_capex_burden_inr * capex_multiplier
            scenario_island_utility += island_utility
            scenario_island_service += island_service
            scenario_island_replacement += island_replacement
            scenario_island_capex += island_capex
            island_scenario_impacts.append(
                UtilityIslandScenarioImpact(
                    island_id=island_cost.island_id,
                    scenario_name=scenario.name,
                    project_capex_burden_inr=round(island_capex, 2),
                    annual_allocated_utility_cost_inr=round(island_utility, 2),
                    annual_service_cost_inr=round(island_service, 2),
                    annual_replacement_cost_inr=round(island_replacement, 2),
                    annual_operating_burden_inr=round(island_utility + island_service + island_replacement, 2),
                    notes=f"Scenario burden for island '{island_cost.island_id}' under {scenario.name}.",
                    citations=island_cost.citations,
                    assumptions=island_cost.assumptions,
                )
            )
        scenario_utility = non_island_utility_cost * (0.55 * scenario.steam_price_multiplier + 0.45 * scenario.power_price_multiplier) + scenario_island_utility
        scenario_raw = raw_material_cost * scenario.feedstock_price_multiplier
        scenario_capex = non_island_capex * scenario.capex_multiplier + scenario_island_capex
        scenario_packing_replacement = annual_packing_replacement_cost * (
            0.75 * scenario.capex_multiplier + 0.25 * scenario.power_price_multiplier
        )
        scenario_classifier_service = annual_classifier_service_cost * (
            0.60 * scenario.capex_multiplier + 0.40 * scenario.power_price_multiplier
        )
        scenario_filter_media = annual_filter_media_replacement_cost * (
            0.80 * scenario.capex_multiplier + 0.20 * scenario.feedstock_price_multiplier
        )
        scenario_dryer_exhaust = annual_dryer_exhaust_treatment_cost * (
            0.45 * scenario.power_price_multiplier + 0.35 * scenario.steam_price_multiplier + 0.20 * scenario.capex_multiplier
        )
        scenario_transport_service = (
            scenario_packing_replacement
            + scenario_classifier_service
            + scenario_filter_media
            + scenario_dryer_exhaust
            + scenario_island_service
            + scenario_island_replacement
        )
        scenario_maint = scenario_capex * 0.028 + scenario_transport_service
        scenario_overheads = 0.19 * (labor_cost + scenario_maint)
        scenario_opex = scenario_raw + scenario_utility + labor_cost + scenario_maint + scenario_overheads
        scenario_revenue = _annual_output_kg(basis) * market.estimated_price_per_kg * scenario.selling_price_multiplier
        scenario_results.append(
            ScenarioResult(
                scenario_name=scenario.name,
                annual_utility_cost_inr=round(scenario_utility, 2),
                annual_transport_service_cost_inr=round(scenario_transport_service, 2),
                annual_utility_island_service_cost_inr=round(scenario_island_service, 2),
                annual_utility_island_replacement_cost_inr=round(scenario_island_replacement, 2),
                annual_utility_island_operating_burden_inr=round(scenario_island_utility + scenario_island_service + scenario_island_replacement, 2),
                annual_packing_replacement_cost_inr=round(scenario_packing_replacement, 2),
                annual_classifier_service_cost_inr=round(scenario_classifier_service, 2),
                annual_filter_media_replacement_cost_inr=round(scenario_filter_media, 2),
                annual_dryer_exhaust_treatment_cost_inr=round(scenario_dryer_exhaust, 2),
                annual_operating_cost_inr=round(scenario_opex, 2),
                annual_revenue_inr=round(scenario_revenue, 2),
                gross_margin_inr=round(scenario_revenue - scenario_opex, 2),
                utility_island_impacts=island_scenario_impacts,
                selected=scenario.name == "base",
            )
        )
    return CostModel(
        currency=basis.currency,
        equipment_purchase_cost=round(purchase_cost, 2),
        installed_cost=round(installed_cost, 2),
        direct_cost=round(direct_cost, 2),
        indirect_cost=round(indirect_cost, 2),
        contingency=round(contingency, 2),
        total_capex=round(total_capex, 2),
        annual_opex=round(annual_opex, 2),
        annual_raw_material_cost=round(raw_material_cost, 2),
        annual_utility_cost=round(utility_cost, 2),
        annual_labor_cost=round(labor_cost, 2),
        annual_maintenance_cost=round(maintenance_cost, 2),
        annual_transport_service_cost=round(transport_service_cost, 2),
        annual_utility_island_service_cost=round(annual_utility_island_service_cost, 2),
        annual_utility_island_replacement_cost=round(annual_utility_island_replacement_cost, 2),
        annual_packing_replacement_cost=round(annual_packing_replacement_cost, 2),
        annual_classifier_service_cost=round(annual_classifier_service_cost, 2),
        annual_filter_media_replacement_cost=round(annual_filter_media_replacement_cost, 2),
        annual_dryer_exhaust_treatment_cost=round(annual_dryer_exhaust_treatment_cost, 2),
        packing_replacement_cycle_years=round(packing_replacement_cycle_years, 3),
        packing_replacement_event_cost=round(packing_replacement_event_cost, 2),
        availability_policy_label=str(availability_policy["label"]),
        planned_minor_outage_days_per_year=float(availability_policy["minor_outage_days"]),
        planned_major_turnaround_days=float(availability_policy["major_turnaround_days"]),
        startup_loss_days_after_turnaround=float(availability_policy["startup_loss_days"]),
        minor_outage_window_note=str(availability_policy["minor_window_note"]),
        major_turnaround_window_note=str(availability_policy["major_window_note"]),
        maintenance_turnaround_cycle_years=maintenance_turnaround_cycle_years,
        maintenance_turnaround_event_cost=round(maintenance_turnaround_event_cost, 2),
        procurement_profile_label=str(procurement_profile["label"]),
        imported_equipment_fraction=round(float(procurement_profile["imported_equipment_fraction"]), 6),
        long_lead_equipment_fraction=round(float(procurement_profile["long_lead_fraction"]), 6),
        construction_months=int(procurement_profile["construction_months"]),
        procurement_advance_fraction=round(float(procurement_profile["advance_fraction"]), 6),
        procurement_progress_fraction=round(float(procurement_profile["progress_fraction"]), 6),
        procurement_retention_fraction=round(float(procurement_profile["retention_fraction"]), 6),
        total_import_duty_inr=round(total_import_duty, 2),
        procurement_schedule=procurement_schedule,
        procurement_package_impacts=procurement_package_impacts,
        annual_overheads=round(overheads, 2),
        route_site_fit_score=round(route_site_fit.overall_fit_score, 3) if route_site_fit is not None else 0.0,
        route_feedstock_cluster_factor=round(route_feedstock_cluster_factor, 6),
        route_logistics_penalty_factor=round(route_logistics_penalty_factor, 6),
        route_batch_penalty_fraction=round(route_batch_penalty_fraction, 6),
        route_solvent_recovery_service_cost_inr=round(route_solvent_recovery_service_cost, 2),
        route_catalyst_service_cost_inr=round(route_catalyst_service_cost, 2),
        route_waste_treatment_burden_inr=round(route_waste_treatment_burden, 2),
        calc_traces=[
            CalcTrace(trace_id="capex", title="Total CAPEX", formula="CAPEX = direct + indirect + contingency", substitutions={"direct": f"{direct_cost:.2f}", "indirect": f"{indirect_cost:.2f}", "contingency": f"{contingency:.2f}"}, result=f"{total_capex:.2f}", units="INR"),
            CalcTrace(
                trace_id="procurement_timing_basis",
                title="Procurement timing basis",
                formula="Procurement timing uses package-family lead times and import content to distribute CAPEX draws across advance, fabrication, delivery, erection, and retention milestones.",
                substitutions={
                    "profile": str(procurement_profile["label"]),
                    "construction_months": str(procurement_profile["construction_months"]),
                    "imported_fraction": f"{float(procurement_profile['imported_equipment_fraction']):.3f}",
                    "long_lead_fraction": f"{float(procurement_profile['long_lead_fraction']):.3f}",
                    "package_families": str(len({item.package_family for item in procurement_package_impacts})),
                    "import_duty": f"{total_import_duty:.2f}",
                    "advance_fraction": f"{float(procurement_profile['advance_fraction']):.3f}",
                    "progress_fraction": f"{float(procurement_profile['progress_fraction']):.3f}",
                    "retention_fraction": f"{float(procurement_profile['retention_fraction']):.3f}",
                },
                result=f"{sum(item['capex_draw_inr'] for item in procurement_schedule):.2f}",
                units="INR",
            ),
            CalcTrace(
                trace_id="procurement_import_duty_basis",
                title="Import-duty burden by equipment class",
                formula="Total import duty = sum(bare equipment cost * import content fraction * import-duty fraction) across procurement package families.",
                substitutions={
                    "package_families": ", ".join(sorted({impact.package_family for impact in procurement_package_impacts})) or "none",
                    "imported_fraction": f"{float(procurement_profile['imported_equipment_fraction']):.3f}",
                },
                result=f"{total_import_duty:.2f}",
                units="INR",
            ),
            CalcTrace(trace_id="opex", title="Annual OPEX", formula="OPEX = RM + utilities + labor + maintenance + overheads", substitutions={"RM": f"{raw_material_cost:.2f}", "utilities": f"{utility_cost:.2f}", "labor": f"{labor_cost:.2f}"}, result=f"{annual_opex:.2f}", units="INR/y"),
            CalcTrace(
                trace_id="route_site_fit_cost_basis",
                title="Route/site-fit cost basis",
                formula="Selected-site logistics and feedstock multipliers are derived from route blueprint complexity, recycle burden, and batch handling fit.",
                substitutions={
                    "site_fit_score": f"{route_site_fit.overall_fit_score:.2f}" if route_site_fit is not None else "0.00",
                    "feedstock_cluster_factor": f"{route_feedstock_cluster_factor:.3f}",
                    "logistics_penalty_factor": f"{route_logistics_penalty_factor:.3f}",
                    "logistics_basis": logistics_basis.selected_candidate_id or "n/a",
                },
                result=f"{direct_cost:.2f}",
                units="INR",
            ),
            CalcTrace(
                trace_id="route_economic_basis",
                title="Route-derived economics basis",
                formula="Raw-material cost and recurring burdens are adjusted using feed complexity, site input cost, batch occupancy, solvent recovery, catalyst, and waste burdens from the selected route blueprint.",
                substitutions={
                    "raw_material_complexity_factor": f"{raw_material_complexity_factor:.3f}",
                    "site_input_cost_factor": f"{site_input_cost_factor:.3f}",
                    "logistics_intensity_factor": f"{logistics_intensity_factor:.3f}",
                    "batch_penalty_fraction": f"{route_batch_penalty_fraction:.3f}",
                    "solvent_recovery_service": f"{route_solvent_recovery_service_cost:.2f}",
                    "catalyst_service": f"{route_catalyst_service_cost:.2f}",
                    "waste_treatment_burden": f"{route_waste_treatment_burden:.2f}",
                },
                result=f"{transport_service_cost:.2f}",
                units="INR/y",
            ),
            CalcTrace(trace_id="integration_train_capex", title="Selected utility-train CAPEX", formula="CAPEX = sum(installed cost of selected utility-train items)", result=f"{utility_train_installed_capex:.2f}", units="INR"),
            CalcTrace(trace_id="transport_penalty_utility_basis", title="Transport-limited utility penalties", formula="Penalty utilities = absorber hydraulic electricity + solids auxiliaries + dryer endpoint steam", substitutions={"steam_load": f"{steam_load:.2f}", "power_load": f"{power_load:.2f}"}, result=f"{utility_cost:.2f}", units="INR/y"),
            CalcTrace(
                trace_id="utility_island_economic_basis",
                title="Utility island economic basis",
                formula="Island economics allocate selected utility-train CAPEX and utility burden across selected utility islands, then add island-specific service costs.",
                substitutions={
                    "selected_islands": str(len(utility_island_costs)),
                    "allocated_utility_cost": f"{sum(item.annual_allocated_utility_cost_inr for item in utility_island_costs):.2f}",
                    "island_service_cost": f"{annual_utility_island_service_cost:.2f}",
                    "island_replacement_cost": f"{annual_utility_island_replacement_cost:.2f}",
                },
                result=f"{sum(item.project_capex_burden_inr for item in utility_island_costs):.2f}",
                units="INR",
            ),
            CalcTrace(
                trace_id="absorber_packing_family_cost_basis",
                title="Absorber packing replacement basis",
                formula="Annual packing replacement = packing inventory * replacement fraction / replacement cycle",
                substitutions={
                    "packing_family": column_design.absorber_packing_family if column_design is not None else "n/a",
                    "specific_area": f"{column_design.absorber_packing_specific_area_m2_m3:.2f}" if column_design is not None else "0.00",
                    "wetting_ratio": f"{column_design.absorber_wetting_ratio:.3f}" if column_design is not None else "0.000",
                    "pressure_drop": f"{column_design.absorber_total_pressure_drop_kpa:.3f}" if column_design is not None else "0.000",
                    "flood_margin": f"{column_design.absorber_flooding_margin_fraction:.3f}" if column_design is not None else "0.000",
                },
                result=f"{annual_packing_replacement_cost:.2f}",
                units="INR/y",
            ),
            CalcTrace(
                trace_id="classifier_service_cost_basis",
                title="Classifier recurring service basis",
                formula="Classifier service = f(slurry circulation, cut size, classification sharpness)",
                substitutions={
                    "slurry_rate": f"{column_design.slurry_circulation_rate_m3_hr:.3f}" if column_design is not None else "0.000",
                    "cut_size": f"{column_design.crystal_classifier_cut_size_mm:.3f}" if column_design is not None else "0.000",
                    "classified_fraction": f"{column_design.crystal_classified_product_fraction:.3f}" if column_design is not None else "0.000",
                },
                result=f"{annual_classifier_service_cost:.2f}",
                units="INR/y",
            ),
            CalcTrace(
                trace_id="filter_media_replacement_basis",
                title="Filter media replacement basis",
                formula="Filter media replacement = f(filter area, cake resistance, medium resistance)",
                substitutions={
                    "filter_area": f"{column_design.filter_area_m2:.3f}" if column_design is not None else "0.000",
                    "alpha_cake": f"{column_design.filter_specific_cake_resistance_m_kg:.3e}" if column_design is not None else "0.000e+00",
                    "Rm": f"{column_design.filter_medium_resistance_1_m:.3e}" if column_design is not None else "0.000e+00",
                },
                result=f"{annual_filter_media_replacement_cost:.2f}",
                units="INR/y",
            ),
            CalcTrace(
                trace_id="dryer_exhaust_treatment_basis",
                title="Dryer exhaust treatment basis",
                formula="Dryer exhaust treatment = f(dry-air flow, humidity lift, exhaust saturation)",
                substitutions={
                    "dry_air": f"{column_design.dryer_dry_air_flow_kg_hr:.3f}" if column_design is not None else "0.000",
                    "humidity_lift": (
                        f"{max(column_design.dryer_exhaust_humidity_ratio_kg_kg - column_design.dryer_inlet_humidity_ratio_kg_kg, 0.0):.4f}"
                        if column_design is not None
                        else "0.0000"
                    ),
                    "exhaust_sat": f"{column_design.dryer_exhaust_saturation_fraction:.3f}" if column_design is not None else "0.000",
                },
                result=f"{annual_dryer_exhaust_treatment_cost:.2f}",
                units="INR/y",
            ),
            CalcTrace(
                trace_id="transport_service_submodel_total",
                title="Recurring transport/service submodel total",
                formula="Transport/service = packing replacement + classifier service + filter media replacement + dryer exhaust treatment",
                substitutions={
                    "packing": f"{annual_packing_replacement_cost:.2f}",
                    "classifier": f"{annual_classifier_service_cost:.2f}",
                    "filter": f"{annual_filter_media_replacement_cost:.2f}",
                    "dryer": f"{annual_dryer_exhaust_treatment_cost:.2f}",
                    "utility_islands": f"{annual_utility_island_service_cost:.2f}",
                    "utility_island_replacement": f"{annual_utility_island_replacement_cost:.2f}",
                },
                result=f"{transport_service_cost:.2f}",
                units="INR/y",
            ),
            CalcTrace(
                trace_id="availability_policy_basis",
                title="Availability policy basis",
                formula="Route-family outage policy defines minor outages, turnaround window, startup loss, and turnaround interval",
                substitutions={
                    "policy": str(availability_policy["label"]),
                    "minor_days": f'{float(availability_policy["minor_outage_days"]):.1f}',
                    "major_days": f'{float(availability_policy["major_turnaround_days"]):.1f}',
                    "startup_loss_days": f'{float(availability_policy["startup_loss_days"]):.1f}',
                    "cycle_years": str(maintenance_turnaround_cycle_years),
                },
                result=f"{maintenance_turnaround_event_cost:.2f}",
                units="INR event",
            ),
        ],
        india_price_data=price_data,
        utility_island_costs=utility_island_costs,
        scenario_results=scenario_results,
        integration_capex_inr=utility_train_installed_capex,
        equipment_cost_items=equipment_cost_items,
        value_records=[
            make_value_record("cost_total_capex", "Total CAPEX", total_capex, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_import_duty_total", "Total import duty", total_import_duty, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_annual_opex", "Annual OPEX", annual_opex, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_logistics_penalty", "Logistics penalty factor", logistics_penalty, "fraction", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_transport_service_penalty", "Annual transport/service penalty cost", transport_service_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_utility_island_service", "Annual utility-island service cost", annual_utility_island_service_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_utility_island_replacement", "Annualized utility-island replacement cost", annual_utility_island_replacement_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_packing_replacement", "Annual packing replacement cost", annual_packing_replacement_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_filter_media_replacement", "Annual filter media replacement cost", annual_filter_media_replacement_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_dryer_exhaust_treatment", "Annual dryer exhaust treatment cost", annual_dryer_exhaust_treatment_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=citations,
        assumptions=assumptions
        + procurement_basis.assumptions
        + logistics_basis.assumptions
        + (["Cost model includes installed equipment implied by the selected utility exchanger train."] if utility_train_items else [])
        + [str(procurement_profile["note"])]
        + [f"Equipment-class procurement package families contribute total import duty INR {total_import_duty:,.2f}."]
        + ["Economics v2 ties CAPEX and OPEX to the selected procurement and logistics basis."],
    )


def build_working_capital_model_v2(
    basis: ProjectBasis,
    cost_model: CostModel,
    market_price_per_kg: float,
    citations: list[str],
    assumptions: list[str],
    operations_planning: OperationsPlanningArtifact | None = None,
) -> WorkingCapitalModel:
    revenue = _annual_output_kg(basis) * market_price_per_kg
    raw_material_days = operations_planning.raw_material_buffer_days + 0.35 * operations_planning.operating_stock_days if operations_planning else 18.0
    product_inventory_days = operations_planning.finished_goods_buffer_days + operations_planning.restart_buffer_days if operations_planning else 10.0
    receivable_days = 32.0
    payable_days = 24.0
    cash_buffer_days = max(7.0, operations_planning.startup_ramp_days + 0.5 * operations_planning.cleaning_downtime_days) if operations_planning else 8.0
    timing_terms = _working_capital_timing_terms(cost_model, operations_planning)
    raw_material_inventory = cost_model.annual_raw_material_cost * raw_material_days / 365.0
    product_inventory = revenue * product_inventory_days / 365.0
    receivables = revenue * receivable_days / 365.0
    payables = cost_model.annual_raw_material_cost * payable_days / 365.0
    cash_buffer = cost_model.annual_opex * cash_buffer_days / 365.0
    restart_loss_inventory = operations_planning.annual_restart_loss_kg * market_price_per_kg if operations_planning else 0.0
    outage_buffer_inventory = (
        cost_model.annual_opex * operations_planning.operating_stock_days * operations_planning.turnaround_buffer_factor / 365.0
        if operations_planning
        else 0.0
    )
    precommissioning_inventory = cost_model.annual_raw_material_cost * float(timing_terms["precommissioning_inventory_days"]) / 365.0
    working_capital = (
        raw_material_inventory
        + product_inventory
        + receivables
        + cash_buffer
        + restart_loss_inventory
        + outage_buffer_inventory
        - payables
    )
    peak_working_capital = max(
        working_capital,
        raw_material_inventory
        + product_inventory * 0.55
        + receivables * 0.35
        + cash_buffer
        + restart_loss_inventory
        + outage_buffer_inventory
        + precommissioning_inventory
        - payables * float(timing_terms["payables_realization_fraction"]),
    )
    return WorkingCapitalModel(
        raw_material_days=raw_material_days,
        product_inventory_days=product_inventory_days,
        receivable_days=receivable_days,
        payable_days=payable_days,
        cash_buffer_days=cash_buffer_days,
        operating_stock_days=operations_planning.operating_stock_days if operations_planning else 0.0,
        procurement_timing_factor=round(float(timing_terms["procurement_timing_factor"]), 3),
        precommissioning_inventory_days=round(float(timing_terms["precommissioning_inventory_days"]), 2),
        precommissioning_inventory_month=round(float(timing_terms["precommissioning_inventory_month"]), 2),
        restart_loss_inventory_inr=round(restart_loss_inventory, 2),
        outage_buffer_inventory_inr=round(outage_buffer_inventory, 2),
        precommissioning_inventory_inr=round(precommissioning_inventory, 2),
        raw_material_inventory_inr=round(raw_material_inventory, 2),
        product_inventory_inr=round(product_inventory, 2),
        receivables_inr=round(receivables, 2),
        payables_inr=round(payables, 2),
        cash_buffer_inr=round(cash_buffer, 2),
        peak_working_capital_month=round(float(timing_terms["peak_working_capital_month"]), 2),
        peak_working_capital_inr=round(peak_working_capital, 2),
        buffer_basis_note=operations_planning.buffer_basis_note if operations_planning else "Working-capital model v2 uses an India manufacturing cash-cycle basis.",
        working_capital_inr=round(working_capital, 2),
        calc_traces=[
            CalcTrace(
                trace_id="wc",
                title="Working capital",
                formula="WC = RM inventory + FG inventory + receivables + cash buffer + restart loss inventory + outage buffer - payables",
                substitutions={
                    "rm_inventory": f"{raw_material_inventory:.2f}",
                    "fg_inventory": f"{product_inventory:.2f}",
                    "receivables": f"{receivables:.2f}",
                    "cash_buffer": f"{cash_buffer:.2f}",
                    "restart_loss_inventory": f"{restart_loss_inventory:.2f}",
                    "outage_buffer_inventory": f"{outage_buffer_inventory:.2f}",
                    "payables": f"{payables:.2f}",
                },
                result=f"{working_capital:.2f}",
                units="INR",
                notes="Operations-planning buffers now feed directly into working capital.",
            ),
            CalcTrace(
                trace_id="wc_procurement_timing",
                title="Procurement-linked peak working-capital basis",
                formula=(
                    "Peak WC = startup inventory bridge + partial receivables/product stock + cash buffer + restart/outage buffers "
                    "- partial payables credit, with the uplift timed by the procurement and construction schedule."
                ),
                substitutions={
                    "timing_factor": f"{float(timing_terms['procurement_timing_factor']):.3f}",
                    "precommissioning_days": f"{float(timing_terms['precommissioning_inventory_days']):.2f}",
                    "precommissioning_month": f"{float(timing_terms['precommissioning_inventory_month']):.2f}",
                    "peak_month": f"{float(timing_terms['peak_working_capital_month']):.2f}",
                    "payables_realization_fraction": f"{float(timing_terms['payables_realization_fraction']):.3f}",
                    "precommissioning_inventory": f"{precommissioning_inventory:.2f}",
                },
                result=f"{peak_working_capital:.2f}",
                units="INR",
                notes="Construction timing now shifts the highest working-capital exposure into the commissioning window.",
            ),
        ],
        value_records=[
            make_value_record("wc_working_capital", "Working capital", working_capital, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("wc_restart_loss_inventory", "Restart loss inventory", restart_loss_inventory, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("wc_outage_buffer_inventory", "Outage buffer inventory", outage_buffer_inventory, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("wc_precommissioning_inventory", "Pre-commissioning inventory", precommissioning_inventory, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("wc_peak_working_capital", "Peak working capital", peak_working_capital, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions
        + [operations_planning.buffer_basis_note if operations_planning else "Working-capital model v2 uses an India manufacturing cash-cycle basis."]
        + [
            (
                f"Procurement-linked working-capital uplift uses construction months {cost_model.construction_months}, "
                f"imported-equipment fraction {cost_model.imported_equipment_fraction:.3f}, and "
                f"long-lead fraction {cost_model.long_lead_equipment_fraction:.3f}."
            )
        ],
    )


def build_financial_model_v2(
    basis: ProjectBasis,
    market_price_per_kg: float,
    cost_model: CostModel,
    working_capital: WorkingCapitalModel,
    citations: list[str],
    assumptions: list[str],
    financing_basis: DecisionRecord,
) -> FinancialModel:
    annual_revenue = _annual_output_kg(basis) * market_price_per_kg
    depreciation = cost_model.total_capex / 12.0
    interest_rate, debt_fraction = _financing_terms(financing_basis)
    construction_funding_schedule, idc_total = _construction_funding_terms(cost_model, interest_rate, debt_fraction)
    total_investment = cost_model.total_capex + working_capital.peak_working_capital_inr + idc_total
    break_even_fraction = min(max(cost_model.annual_opex / max(annual_revenue, 1.0), 0.0), 1.5)
    annual_schedule: list[dict[str, float | str]] = []
    capacity_profile = [0.80, 0.85] + [0.90] * 10
    debt_entries = _build_debt_entries(
        cost_model.total_capex * debt_fraction + idc_total,
        interest_rate,
        min(len(capacity_profile), 5),
        citations + financing_basis.citations,
        assumptions + financing_basis.assumptions,
    )
    base_maintenance_cost = max(cost_model.annual_maintenance_cost - cost_model.annual_transport_service_cost, 0.0)
    packing_cycle_year = max(int(round(cost_model.packing_replacement_cycle_years)), 0)
    turnaround_cycle_year = max(cost_model.maintenance_turnaround_cycle_years, 0)
    island_cycle_years = {
        item.island_id: max(int(round(item.maintenance_cycle_years)), 0)
        for item in cost_model.utility_island_costs
    }
    minor_outage_days = cost_model.planned_minor_outage_days_per_year
    major_turnaround_days_basis = cost_model.planned_major_turnaround_days
    startup_loss_days_basis = cost_model.startup_loss_days_after_turnaround
    annual_operating_days = basis.annual_operating_days
    discount_rate = 0.12
    discounted_operating_cashflows = 0.0
    cumulative_cash = -total_investment
    payback_years: float | None = None
    last_year_cash = 1.0
    dscr_values: list[float] = []
    cfads_values: list[float] = []
    for year_index, utilization in enumerate(capacity_profile, start=1):
        debt_entry = debt_entries[year_index - 1] if year_index - 1 < len(debt_entries) else None
        turnaround_due = turnaround_cycle_year > 0 and year_index % turnaround_cycle_year == 0
        packing_due = packing_cycle_year > 0 and year_index % packing_cycle_year == 0
        due_island_costs = [
            item
            for item in cost_model.utility_island_costs
            if island_cycle_years.get(item.island_id, 0) > 0 and year_index % island_cycle_years[item.island_id] == 0
        ]
        year_utility_island_replacement = sum(item.replacement_event_cost_inr for item in due_island_costs)
        year_utility_island_turnaround = sum(item.replacement_event_cost_inr * 0.12 for item in due_island_costs)
        year_utility_island_turnaround_days = sum(item.planned_turnaround_days for item in due_island_costs)
        year_major_turnaround_days = (major_turnaround_days_basis if turnaround_due else 0.0) + year_utility_island_turnaround_days
        year_startup_loss_days = startup_loss_days_basis if turnaround_due else 0.0
        available_operating_days = max(
            annual_operating_days - minor_outage_days - year_major_turnaround_days - year_startup_loss_days,
            annual_operating_days * 0.70,
        )
        availability_fraction = available_operating_days / max(annual_operating_days, 1.0)
        effective_utilization = max(utilization * availability_fraction, 0.65)
        base_revenue_without_outages = annual_revenue * utilization
        revenue_loss_from_outages = max(base_revenue_without_outages - annual_revenue * effective_utilization, 0.0)
        outage_calendar_note = (
            f"{cost_model.minor_outage_window_note} "
            f"{cost_model.major_turnaround_window_note if turnaround_due else 'No major turnaround scheduled this year.'}"
        ).strip()
        year_revenue = annual_revenue * effective_utilization
        year_raw_material = cost_model.annual_raw_material_cost * effective_utilization
        year_utility = cost_model.annual_utility_cost * (0.82 + 0.18 * effective_utilization)
        year_labor = cost_model.annual_labor_cost * (0.96 + 0.04 * effective_utilization)
        year_base_maintenance = base_maintenance_cost * (0.88 + 0.12 * effective_utilization)
        year_classifier_service = cost_model.annual_classifier_service_cost * (0.72 + 0.28 * effective_utilization)
        year_filter_media = cost_model.annual_filter_media_replacement_cost * (0.70 + 0.30 * effective_utilization)
        year_dryer_exhaust = cost_model.annual_dryer_exhaust_treatment_cost * (0.68 + 0.32 * effective_utilization)
        year_utility_island_service = cost_model.annual_utility_island_service_cost * (0.75 + 0.25 * effective_utilization)
        year_packing_replacement = cost_model.packing_replacement_event_cost if packing_due else 0.0
        year_turnaround = cost_model.maintenance_turnaround_event_cost if turnaround_due else 0.0
        year_transport_service = (
            year_packing_replacement
            + year_classifier_service
            + year_filter_media
            + year_dryer_exhaust
            + year_utility_island_service
            + year_utility_island_replacement
        )
        year_maintenance_total = year_base_maintenance + year_transport_service + year_turnaround + year_utility_island_turnaround
        year_overheads = 0.19 * (year_labor + year_maintenance_total)
        year_opex = year_raw_material + year_utility + year_labor + year_maintenance_total + year_overheads
        year_depreciation = depreciation
        year_interest = debt_entry.interest_inr if debt_entry is not None else 0.0
        principal_repayment = debt_entry.principal_repayment_inr if debt_entry is not None else 0.0
        debt_service = principal_repayment + year_interest
        year_pbt = year_revenue - year_opex - year_depreciation - year_interest
        year_tax = max(year_pbt, 0.0) * 0.25
        year_pat = year_pbt - year_tax
        year_cash = year_pat + year_depreciation
        normalized_opex_for_dscr = (
            year_raw_material
            + year_utility
            + year_labor
            + year_base_maintenance
            + year_classifier_service
            + year_filter_media
            + year_dryer_exhaust
            + year_utility_island_service
            + year_overheads
        )
        cfads = max(year_revenue - normalized_opex_for_dscr - year_tax, 0.0)
        cfads_values.append(cfads)
        dscr = max(cfads / debt_service, 0.05) if debt_service > 0.0 else 0.0
        if debt_service > 0.0:
            dscr_values.append(dscr)
        last_year_cash = max(year_cash, 1.0)
        discounted_operating_cashflows += year_cash / ((1.0 + discount_rate) ** year_index)
        if payback_years is None:
            previous_cumulative_cash = cumulative_cash
            cumulative_cash += year_cash
            if cumulative_cash >= 0.0:
                payback_years = (year_index - 1) + abs(previous_cumulative_cash) / max(year_cash, 1.0)
        else:
            cumulative_cash += year_cash
        annual_schedule.append(
            {
                "year": year_index,
                "capacity_utilization_pct": round(effective_utilization * 100.0, 2),
                "availability_pct": round(availability_fraction * 100.0, 2),
                "minor_outage_days": round(minor_outage_days, 2),
                "major_turnaround_days": round(year_major_turnaround_days, 2),
                "startup_loss_days": round(year_startup_loss_days, 2),
                "available_operating_days": round(available_operating_days, 2),
                "outage_calendar_note": outage_calendar_note,
                "revenue_loss_from_outages_inr": round(revenue_loss_from_outages, 2),
                "capex_draw_inr": 0.0,
                "debt_draw_inr": 0.0,
                "equity_draw_inr": 0.0,
                "idc_inr": 0.0,
                "revenue_inr": round(year_revenue, 2),
                "raw_material_cost_inr": round(year_raw_material, 2),
                "utility_cost_inr": round(year_utility, 2),
                "labor_cost_inr": round(year_labor, 2),
                "base_maintenance_inr": round(year_base_maintenance, 2),
                "transport_service_cost_inr": round(year_transport_service, 2),
                "utility_island_service_cost_inr": round(year_utility_island_service, 2),
                "utility_island_replacement_cost_inr": round(year_utility_island_replacement, 2),
                "packing_replacement_cost_inr": round(year_packing_replacement, 2),
                "classifier_service_cost_inr": round(year_classifier_service, 2),
                "filter_media_replacement_cost_inr": round(year_filter_media, 2),
                "dryer_exhaust_treatment_cost_inr": round(year_dryer_exhaust, 2),
                "turnaround_cost_inr": round(year_turnaround, 2),
                "utility_island_turnaround_cost_inr": round(year_utility_island_turnaround, 2),
                "turnaround_flag": "yes" if turnaround_due else "no",
                "principal_repayment_inr": round(principal_repayment, 2),
                "debt_service_inr": round(debt_service, 2),
                "dscr": round(dscr, 3),
                "cfads_inr": round(cfads, 2),
                "operating_cost_inr": round(year_opex, 2),
                "interest_inr": round(year_interest, 2),
                "depreciation_inr": round(year_depreciation, 2),
                "profit_before_tax_inr": round(year_pbt, 2),
                "tax_inr": round(year_tax, 2),
                "profit_after_tax_inr": round(year_pat, 2),
                "cash_accrual_inr": round(year_cash, 2),
            }
        )
    annual_cashflow = max(last_year_cash, 1.0)
    npv = -total_investment + discounted_operating_cashflows
    profitability_index = discounted_operating_cashflows / max(total_investment, 1.0)
    if payback_years is None:
        payback_years = total_investment / annual_cashflow
    low_rate = 0.0
    high_rate = 0.60
    irr = 0.0
    for _ in range(40):
        trial_rate = (low_rate + high_rate) / 2.0
        trial_npv = -total_investment
        for year_index, row in enumerate(annual_schedule, start=1):
            trial_npv += float(row["cash_accrual_inr"]) / ((1.0 + trial_rate) ** year_index)
        if trial_npv > 0.0:
            low_rate = trial_rate
        else:
            high_rate = trial_rate
        irr = trial_rate
    if irr <= 0.0001:
        irr = min(max((annual_cashflow / max(total_investment, 1.0)) * 0.82, 0.01), 0.45)
    irr *= 100.0
    minimum_dscr = min(dscr_values) if dscr_values else 0.0
    average_dscr = sum(dscr_values) / len(dscr_values) if dscr_values else 0.0
    opening_debt = debt_entries[0].opening_debt_inr if debt_entries else 0.0
    loan_life_years = len(debt_entries)
    loan_life_cfads_pv = sum(
        cfads_values[index] / ((1.0 + interest_rate) ** (index + 1))
        for index in range(min(loan_life_years, len(cfads_values)))
    )
    project_life_cfads_pv = sum(
        cfads / ((1.0 + interest_rate) ** year_index)
        for year_index, cfads in enumerate(cfads_values, start=1)
    )
    llcr = loan_life_cfads_pv / max(opening_debt, 1.0) if opening_debt > 0.0 else 0.0
    plcr = project_life_cfads_pv / max(opening_debt, 1.0) if opening_debt > 0.0 else 0.0
    has_debt = opening_debt > 0.0 and bool(dscr_values or debt_entries)
    covenant_breach_codes = _coverage_breach_codes(minimum_dscr, average_dscr, llcr, plcr, has_debt=has_debt)
    covenant_warnings = _breach_warning_messages(minimum_dscr, average_dscr, llcr, plcr, has_debt=has_debt)
    return FinancialModel(
        currency=basis.currency,
        annual_revenue=round(annual_revenue, 2),
        annual_operating_cost=round(cost_model.annual_opex, 2),
        gross_profit=round(annual_revenue - cost_model.annual_opex, 2),
        working_capital=round(working_capital.working_capital_inr, 2),
        peak_working_capital_inr=round(working_capital.peak_working_capital_inr, 2),
        peak_working_capital_month=round(working_capital.peak_working_capital_month, 2),
        payback_years=round(payback_years, 3),
        npv=round(npv, 2),
        irr=round(irr, 2),
        profitability_index=round(profitability_index, 3),
        break_even_fraction=round(break_even_fraction, 3),
        total_project_funding_inr=round(total_investment, 2),
        construction_interest_during_construction_inr=round(idc_total, 2),
        minimum_dscr=round(minimum_dscr, 3),
        average_dscr=round(average_dscr, 3),
        llcr=round(llcr, 3),
        plcr=round(plcr, 3),
        selected_financing_candidate_id=financing_basis.selected_candidate_id or "",
        selected_financing_description=financing_basis.selected_summary,
        covenant_breach_codes=covenant_breach_codes,
        covenant_warnings=covenant_warnings,
        annual_schedule=annual_schedule,
        calc_traces=[
            CalcTrace(trace_id="financial_cashflow", title="Annual cashflow", formula="Cashflow = PBT - tax + depreciation", result=f"{annual_cashflow:.2f}", units="INR/y"),
            CalcTrace(trace_id="financial_payback", title="Payback", formula="Payback uses cumulative yearwise cash accrual including replacement and turnaround events", result=f"{payback_years:.3f}", units="y"),
            CalcTrace(trace_id="financial_turnaround_schedule", title="Recurring maintenance timing basis", formula="Yearwise OPEX includes discrete packing replacement, utility-island replacement, and turnaround events instead of a flat annualized maintenance burden", substitutions={"packing_cycle_years": f"{cost_model.packing_replacement_cycle_years:.2f}", "utility_island_cycle_years": ", ".join(f"{item.island_id}:{item.maintenance_cycle_years:.2f}" for item in cost_model.utility_island_costs) or "none", "turnaround_cycle_years": str(cost_model.maintenance_turnaround_cycle_years)}, result=f"{cost_model.maintenance_turnaround_event_cost:.2f}", units="INR event"),
            CalcTrace(
                trace_id="financial_procurement_timing",
                title="Construction funding timing basis",
                formula="Construction funding uses staged procurement draws, procurement-linked peak working capital, and interest during construction before operations start.",
                substitutions={
                    "procurement_profile": cost_model.procurement_profile_label,
                    "construction_months": str(cost_model.construction_months),
                    "peak_working_capital": f"{working_capital.peak_working_capital_inr:,.2f}",
                    "peak_working_capital_month": f"{working_capital.peak_working_capital_month:.2f}",
                    "debt_fraction": f"{debt_fraction:.3f}",
                    "interest_rate": f"{interest_rate:.4f}",
                    "draws": "; ".join(
                        f"{row['milestone']}@m{row['month']}:INR {float(row['capex_draw_inr']):,.0f}"
                        for row in construction_funding_schedule
                    ) or "none",
                },
                result=f"{idc_total:.2f}",
                units="INR",
            ),
            CalcTrace(
                trace_id="financial_dscr_basis",
                title="Debt-service coverage basis",
                formula="DSCR = CFADS / debt service, where CFADS = revenue - opex - tax and debt service = principal + interest.",
                substitutions={
                    "minimum_dscr": f"{minimum_dscr:.3f}",
                    "average_dscr": f"{average_dscr:.3f}",
                    "debt_years": str(len(debt_entries)),
                },
                result=f"{minimum_dscr:.3f}",
                units="ratio",
            ),
            CalcTrace(
                trace_id="financial_lender_coverage_basis",
                title="Lender-style coverage basis",
                formula="LLCR = PV(loan-life CFADS) / opening debt and PLCR = PV(project-life CFADS) / opening debt, discounted at the debt screening rate.",
                substitutions={
                    "opening_debt": f"{opening_debt:.2f}",
                    "debt_years": str(loan_life_years),
                    "loan_life_cfads_pv": f"{loan_life_cfads_pv:.2f}",
                    "project_life_cfads_pv": f"{project_life_cfads_pv:.2f}",
                    "discount_rate": f"{interest_rate:.4f}",
                },
                result=f"LLCR={llcr:.3f}; PLCR={plcr:.3f}",
                units="ratio",
            ),
        ],
        scenario_results=cost_model.scenario_results,
        value_records=[
            make_value_record("financial_revenue", "Annual revenue", annual_revenue, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_payback", "Payback", payback_years, "y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_irr", "IRR", irr, "%", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_idc", "Interest during construction", idc_total, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("financial_peak_working_capital", "Peak working capital", working_capital.peak_working_capital_inr, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_minimum_dscr", "Minimum DSCR", minimum_dscr, "ratio", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_llcr", "LLCR", llcr, "ratio", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_plcr", "PLCR", plcr, "ratio", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions
        + financing_basis.assumptions
        + ["Financial model v2 includes procurement-timed funding, procurement-linked peak working capital, interest during construction, depreciation, interest, tax, DSCR, LLCR, and PLCR screening."],
    )


def build_economic_scenario_model_v2(
    cost_model: CostModel,
    financial_model: FinancialModel,
    economic_basis: DecisionRecord,
) -> EconomicScenarioModel:
    rows = [
        f"| {scenario.scenario_name} | {scenario.annual_revenue_inr:,.2f} | {scenario.annual_transport_service_cost_inr:,.2f} | {scenario.annual_utility_island_operating_burden_inr:,.2f} | {scenario.annual_operating_cost_inr:,.2f} | {scenario.gross_margin_inr:,.2f} |"
        for scenario in financial_model.scenario_results
    ]
    markdown = "\n".join(
        [
            "| Scenario | Revenue (INR/y) | Transport/Service (INR/y) | Utility-Island Burden (INR/y) | Opex (INR/y) | Gross Margin (INR/y) |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )
    if any(scenario.annual_transport_service_cost_inr > 0.0 for scenario in financial_model.scenario_results):
        breakdown_rows = [
            f"| {scenario.scenario_name} | {scenario.annual_utility_island_service_cost_inr:,.2f} | {scenario.annual_utility_island_replacement_cost_inr:,.2f} | {scenario.annual_packing_replacement_cost_inr:,.2f} | {scenario.annual_classifier_service_cost_inr:,.2f} | {scenario.annual_filter_media_replacement_cost_inr:,.2f} | {scenario.annual_dryer_exhaust_treatment_cost_inr:,.2f} |"
            for scenario in financial_model.scenario_results
        ]
        markdown += "\n\n" + "\n".join(
            [
                "| Scenario | Utility-Island Service (INR/y) | Utility-Island Replacement (INR/y) | Packing (INR/y) | Classifier (INR/y) | Filter Media (INR/y) | Dryer Exhaust (INR/y) |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                *breakdown_rows,
            ]
        )
    island_rows = [
        f"| {scenario.scenario_name} | {impact.island_id} | {impact.project_capex_burden_inr:,.2f} | {impact.annual_allocated_utility_cost_inr:,.2f} | {impact.annual_service_cost_inr:,.2f} | {impact.annual_replacement_cost_inr:,.2f} | {impact.annual_operating_burden_inr:,.2f} |"
        for scenario in financial_model.scenario_results
        for impact in scenario.utility_island_impacts
    ]
    if island_rows:
        markdown += "\n\n" + "\n".join(
            [
                "| Scenario | Island | Capex Burden (INR) | Allocated Utility (INR/y) | Service (INR/y) | Replacement (INR/y) | Operating Burden (INR/y) |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                *island_rows,
            ]
        )
    return EconomicScenarioModel(
        selected_basis_decision_id=economic_basis.decision_id,
        scenarios=financial_model.scenario_results,
        markdown=markdown,
        citations=cost_model.citations,
        assumptions=cost_model.assumptions + financial_model.assumptions + economic_basis.assumptions,
    )


def build_plant_cost_summary(cost_model: CostModel, working_capital: WorkingCapitalModel | None = None) -> PlantCostSummary:
    breakdowns: list[EquipmentCostBreakdown] = []
    direct_cost_accumulator = 0.0
    for item in cost_model.equipment_cost_items:
        installation = max(item.installed_cost_inr - item.bare_cost_inr, 0.0) * 0.42
        piping = item.installed_cost_inr * 0.14
        instrumentation = item.installed_cost_inr * 0.08
        electrical = item.installed_cost_inr * 0.06
        civil = item.installed_cost_inr * 0.12
        insulation = item.installed_cost_inr * 0.04
        contingency = item.installed_cost_inr * 0.05
        total_installed = item.bare_cost_inr + installation + piping + instrumentation + electrical + civil + insulation + contingency
        direct_cost_accumulator += total_installed
        breakdowns.append(
            EquipmentCostBreakdown(
                equipment_id=item.equipment_id,
                bare_cost_inr=round(item.bare_cost_inr, 2),
                installation_inr=round(installation, 2),
                piping_inr=round(piping, 2),
                instrumentation_inr=round(instrumentation, 2),
                electrical_inr=round(electrical, 2),
                civil_structural_inr=round(civil, 2),
                insulation_painting_inr=round(insulation, 2),
                contingency_inr=round(contingency, 2),
                total_installed_inr=round(total_installed, 2),
                citations=item.citations,
                assumptions=item.assumptions,
            )
        )
    indirect = cost_model.indirect_cost
    working_capital_inr = working_capital.working_capital_inr if working_capital else 0.0
    total_project_cost = direct_cost_accumulator + indirect + cost_model.contingency + working_capital_inr
    markdown_rows = [
        [
            item.equipment_id,
            f"{item.bare_cost_inr:,.2f}",
            f"{item.installation_inr:,.2f}",
            f"{item.piping_inr:,.2f}",
            f"{item.instrumentation_inr:,.2f}",
            f"{item.total_installed_inr:,.2f}",
        ]
        for item in breakdowns
    ]
    markdown = "\n".join(
        [
            "| Equipment | Bare | Installation | Piping | Instrumentation | Total Installed |",
            "| --- | --- | --- | --- | --- | --- |",
            *[
                f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |"
                for row in markdown_rows
            ],
        ]
    )
    return PlantCostSummary(
        currency=cost_model.currency,
        equipment_breakdowns=breakdowns,
        direct_plant_cost_inr=round(direct_cost_accumulator, 2),
        indirect_cost_inr=round(indirect, 2),
        contingency_inr=round(cost_model.contingency, 2),
        working_capital_inr=round(working_capital_inr, 2),
        total_project_cost_inr=round(total_project_cost, 2),
        markdown=markdown,
        citations=cost_model.citations + (working_capital.citations if working_capital else []),
        assumptions=cost_model.assumptions + (working_capital.assumptions if working_capital else []) + ["Plant-cost summary allocates installed cost into industrial screening buckets."],
    )


def build_debt_schedule(cost_model: CostModel, financing_basis: DecisionRecord, years: int = 5) -> DebtSchedule:
    interest_rate, debt_fraction = _financing_terms(financing_basis)
    _, idc_total = _construction_funding_terms(cost_model, interest_rate, debt_fraction)
    opening_debt = cost_model.total_capex * debt_fraction + idc_total
    entries = _build_debt_entries(
        opening_debt,
        interest_rate,
        years,
        cost_model.citations + financing_basis.citations,
        cost_model.assumptions + financing_basis.assumptions,
    )
    markdown = "\n".join(
        [
            "| Year | Opening Debt | Principal | Interest | Closing Debt |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {entry.year} | {entry.opening_debt_inr:,.2f} | {entry.principal_repayment_inr:,.2f} | {entry.interest_inr:,.2f} | {entry.closing_debt_inr:,.2f} |"
                for entry in entries
            ],
        ]
    )
    return DebtSchedule(
        debt_fraction=debt_fraction,
        interest_rate=interest_rate,
        entries=entries,
        markdown=markdown,
        citations=cost_model.citations + financing_basis.citations,
        assumptions=cost_model.assumptions + financing_basis.assumptions,
    )


def build_tax_depreciation_basis(cost_model: CostModel) -> TaxDepreciationBasis:
    return TaxDepreciationBasis(
        depreciation_method="Straight line screening basis",
        depreciation_years=12,
        tax_rate_fraction=0.25,
        markdown=(
            f"Depreciation uses a 12-year straight-line screening basis on total CAPEX of INR {cost_model.total_capex:,.2f}; "
            "corporate tax assumed at 25%."
        ),
        citations=cost_model.citations,
        assumptions=cost_model.assumptions + ["Tax and depreciation remain screening-level and India-grounded."],
    )


def build_financial_schedule(financial_model: FinancialModel) -> FinancialSchedule:
    lines = [
        FinancialScheduleLine(
            year=int(row["year"]),
            capacity_utilization_pct=float(row["capacity_utilization_pct"]),
            availability_pct=float(row.get("availability_pct", 0.0)),
            minor_outage_days=float(row.get("minor_outage_days", 0.0)),
            major_turnaround_days=float(row.get("major_turnaround_days", 0.0)),
            startup_loss_days=float(row.get("startup_loss_days", 0.0)),
            available_operating_days=float(row.get("available_operating_days", 0.0)),
            outage_calendar_note=str(row.get("outage_calendar_note", "")),
            revenue_loss_from_outages_inr=float(row.get("revenue_loss_from_outages_inr", 0.0)),
            capex_draw_inr=float(row.get("capex_draw_inr", 0.0)),
            debt_draw_inr=float(row.get("debt_draw_inr", 0.0)),
            equity_draw_inr=float(row.get("equity_draw_inr", 0.0)),
            idc_inr=float(row.get("idc_inr", 0.0)),
            revenue_inr=float(row["revenue_inr"]),
            operating_cost_inr=float(row["operating_cost_inr"]),
            raw_material_cost_inr=float(row.get("raw_material_cost_inr", 0.0)),
            utility_cost_inr=float(row.get("utility_cost_inr", 0.0)),
            labor_cost_inr=float(row.get("labor_cost_inr", 0.0)),
            base_maintenance_inr=float(row.get("base_maintenance_inr", 0.0)),
            transport_service_cost_inr=float(row.get("transport_service_cost_inr", 0.0)),
            utility_island_service_cost_inr=float(row.get("utility_island_service_cost_inr", 0.0)),
            utility_island_replacement_cost_inr=float(row.get("utility_island_replacement_cost_inr", 0.0)),
            packing_replacement_cost_inr=float(row.get("packing_replacement_cost_inr", 0.0)),
            classifier_service_cost_inr=float(row.get("classifier_service_cost_inr", 0.0)),
            filter_media_replacement_cost_inr=float(row.get("filter_media_replacement_cost_inr", 0.0)),
            dryer_exhaust_treatment_cost_inr=float(row.get("dryer_exhaust_treatment_cost_inr", 0.0)),
            turnaround_cost_inr=float(row.get("turnaround_cost_inr", 0.0)),
            utility_island_turnaround_cost_inr=float(row.get("utility_island_turnaround_cost_inr", 0.0)),
            turnaround_flag=str(row.get("turnaround_flag", "no")).lower() == "yes",
            principal_repayment_inr=float(row.get("principal_repayment_inr", 0.0)),
            debt_service_inr=float(row.get("debt_service_inr", 0.0)),
            dscr=float(row.get("dscr", 0.0)),
            cfads_inr=float(row.get("cfads_inr", 0.0)),
            depreciation_inr=float(row["depreciation_inr"]),
            interest_inr=float(row["interest_inr"]),
            profit_before_tax_inr=float(row["profit_before_tax_inr"]),
            tax_inr=float(row["tax_inr"]),
            profit_after_tax_inr=float(row["profit_after_tax_inr"]),
            cash_accrual_inr=float(row["cash_accrual_inr"]),
            citations=financial_model.citations,
            assumptions=financial_model.assumptions,
        )
        for row in financial_model.annual_schedule
    ]
    markdown = "\n".join(
        [
            "| Year | Utilization (%) | Availability (%) | Minor Outage (d) | Turnaround (d) | Startup Loss (d) | Revenue Loss | Revenue | Opex | CFADS | Debt Service | DSCR | Transport/Service | Utility-Island Service | Utility-Island Replacement | Packing | Turnaround Cost | Utility-Island Turnaround | Depreciation | Interest | Principal | PBT | Tax | PAT | Cash Accrual |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {line.year} | {line.capacity_utilization_pct:.2f} | {line.availability_pct:.2f} | {line.minor_outage_days:.2f} | {line.major_turnaround_days:.2f} | {line.startup_loss_days:.2f} | {line.revenue_loss_from_outages_inr:,.2f} | {line.revenue_inr:,.2f} | {line.operating_cost_inr:,.2f} | {line.cfads_inr:,.2f} | {line.debt_service_inr:,.2f} | {line.dscr:.3f} | {line.transport_service_cost_inr:,.2f} | {line.utility_island_service_cost_inr:,.2f} | {line.utility_island_replacement_cost_inr:,.2f} | {line.packing_replacement_cost_inr:,.2f} | {line.turnaround_cost_inr:,.2f} | {line.utility_island_turnaround_cost_inr:,.2f} | {line.depreciation_inr:,.2f} | {line.interest_inr:,.2f} | {line.principal_repayment_inr:,.2f} | {line.profit_before_tax_inr:,.2f} | {line.tax_inr:,.2f} | {line.profit_after_tax_inr:,.2f} | {line.cash_accrual_inr:,.2f} |"
                for line in lines
            ],
        ]
    )
    return FinancialSchedule(
        currency=financial_model.currency,
        lines=lines,
        markdown=markdown,
        citations=financial_model.citations,
        assumptions=financial_model.assumptions,
    )
