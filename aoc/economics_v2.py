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
    PlantCostSummary,
    ProjectBasis,
    ScenarioStability,
    ScenarioPolicy,
    ScenarioResult,
    SensitivityLevel,
    SiteSelectionArtifact,
    StreamTable,
    TaxDepreciationBasis,
    UtilityArchitectureDecision,
    UtilitySummaryArtifact,
    WorkingCapitalModel,
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


def _utility_train_cost_items(
    utility_architecture: UtilityArchitectureDecision | None,
    citations: list[str],
    assumptions: list[str],
) -> tuple[list[EquipmentCostItem], float]:
    if utility_architecture is None or not utility_architecture.architecture.selected_package_items:
        return [], 0.0
    items: list[EquipmentCostItem] = []
    installed_total = 0.0
    for package_item in utility_architecture.architecture.selected_package_items:
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
        else:
            base_cost = 650_000.0 + max(package_item.design_pressure_bar, 1.0) * 85000.0
            install_factor = 1.60
        installed_cost = base_cost * install_factor
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
                bare_cost_inr=round(base_cost, 2),
                installed_cost_inr=round(installed_cost, 2),
                spares_cost_inr=round(base_cost * 0.02, 2),
                notes="Utility-train package cost item derived from the selected package inventory.",
                citations=sorted(set(citations + package_item.citations)),
                assumptions=sorted(set(assumptions + package_item.assumptions)),
            )
        )
    return items, round(installed_total, 2)


def build_procurement_basis_decision(site: SiteSelectionArtifact, equipment: list[EquipmentSpec]) -> DecisionRecord:
    coastal = "port" in " ".join(location.port_access.lower() for location in site.india_location_data)
    options = [
        AlternativeOption(candidate_id="domestic_cluster_procurement", candidate_type="procurement_basis", description="Domestic cluster-led procurement", total_score=92.0 if coastal else 86.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="mixed_import_domestic", candidate_type="procurement_basis", description="Mixed import and domestic procurement", total_score=84.0 if coastal else 72.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="import_heavy", candidate_type="procurement_basis", description="Import-heavy procurement", total_score=68.0 if coastal else 55.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
    ]
    return _decision("procurement_basis", f"Procurement basis for {site.selected_site} and {len(equipment)} equipment items.", options, site.citations, site.assumptions)


def build_financing_basis_decision(basis: ProjectBasis, site: SiteSelectionArtifact) -> DecisionRecord:
    options = [
        AlternativeOption(candidate_id="debt_equity_70_30", candidate_type="financing_basis", description="70:30 debt-equity basis", total_score=90.0 if basis.capacity_tpa >= 100000 else 82.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="debt_equity_60_40", candidate_type="financing_basis", description="60:40 debt-equity basis", total_score=86.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
        AlternativeOption(candidate_id="conservative_50_50", candidate_type="financing_basis", description="50:50 conservative financing basis", total_score=72.0, feasible=True, citations=site.citations, assumptions=site.assumptions),
    ]
    return _decision("financing_basis", f"Financing basis for {basis.target_product} in India.", options, site.citations, site.assumptions)


def build_logistics_basis_decision(site: SiteSelectionArtifact, market: MarketAssessmentArtifact) -> DecisionRecord:
    coastal = site.selected_site.lower() in {"dahej", "jamnagar", "paradip"}
    options = [
        AlternativeOption(candidate_id="coastal_cluster_dispatch", candidate_type="logistics_basis", description="Coastal cluster dispatch basis", total_score=92.0 if coastal else 70.0, feasible=True, citations=site.citations + market.citations, assumptions=site.assumptions + market.assumptions),
        AlternativeOption(candidate_id="rail_road_inland", candidate_type="logistics_basis", description="Rail-road inland dispatch basis", total_score=84.0 if not coastal else 78.0, feasible=True, citations=site.citations + market.citations, assumptions=site.assumptions + market.assumptions),
    ]
    return _decision("logistics_basis", f"Logistics basis for {site.selected_site}.", options, site.citations + market.citations, site.assumptions + market.assumptions)


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
    packing_replacement_cycle_years = 0.0
    packing_replacement_event_cost = 0.0
    availability_policy = _availability_policy_for_cost_model(column_design)
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
        bare_cost = max(2_500_000.0, (item.volume_m3 * equipment_factor + item.duty_kw * 1800.0) * capex_multiplier)
        installed_item_cost = bare_cost * installed_multiplier
        spares_cost = bare_cost * spares_fraction
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
    utility_train_items, utility_train_installed_capex = _utility_train_cost_items(utility_architecture, citations, assumptions)
    if utility_train_items:
        equipment_cost_items.extend(utility_train_items)
        purchase_cost += sum(item.bare_cost_inr for item in utility_train_items)
    installed_factor = 2.15 if procurement_basis.selected_candidate_id == "domestic_cluster_procurement" else 2.35
    logistics_penalty = 0.02 if logistics_basis.selected_candidate_id == "coastal_cluster_dispatch" else 0.06
    installed_cost = purchase_cost * installed_factor
    direct_cost = installed_cost * (1.14 + logistics_penalty)
    indirect_cost = direct_cost * 0.24
    contingency = direct_cost * 0.10
    total_capex = direct_cost + indirect_cost + contingency
    feed_mass = sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_id.startswith("S-10")
        for component in stream.components
    ) * annual_hours
    benchmark_raw_material_price = market.estimated_price_per_kg * 0.58
    raw_material_cost = feed_mass * benchmark_raw_material_price
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
    labor_cost = 240.0 * _find_price(price_data, "Operating labour", 650000.0)
    transport_service_cost = (
        annual_packing_replacement_cost
        + annual_classifier_service_cost
        + annual_filter_media_replacement_cost
        + annual_dryer_exhaust_treatment_cost
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
    scenario_results: list[ScenarioResult] = []
    for scenario in scenario_policy.cases:
        scenario_utility = utility_cost * (0.55 * scenario.steam_price_multiplier + 0.45 * scenario.power_price_multiplier)
        scenario_raw = raw_material_cost * scenario.feedstock_price_multiplier
        scenario_capex = total_capex * scenario.capex_multiplier
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
                annual_packing_replacement_cost_inr=round(scenario_packing_replacement, 2),
                annual_classifier_service_cost_inr=round(scenario_classifier_service, 2),
                annual_filter_media_replacement_cost_inr=round(scenario_filter_media, 2),
                annual_dryer_exhaust_treatment_cost_inr=round(scenario_dryer_exhaust, 2),
                annual_operating_cost_inr=round(scenario_opex, 2),
                annual_revenue_inr=round(scenario_revenue, 2),
                gross_margin_inr=round(scenario_revenue - scenario_opex, 2),
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
        annual_overheads=round(overheads, 2),
        calc_traces=[
            CalcTrace(trace_id="capex", title="Total CAPEX", formula="CAPEX = direct + indirect + contingency", substitutions={"direct": f"{direct_cost:.2f}", "indirect": f"{indirect_cost:.2f}", "contingency": f"{contingency:.2f}"}, result=f"{total_capex:.2f}", units="INR"),
            CalcTrace(trace_id="opex", title="Annual OPEX", formula="OPEX = RM + utilities + labor + maintenance + overheads", substitutions={"RM": f"{raw_material_cost:.2f}", "utilities": f"{utility_cost:.2f}", "labor": f"{labor_cost:.2f}"}, result=f"{annual_opex:.2f}", units="INR/y"),
            CalcTrace(trace_id="integration_train_capex", title="Selected utility-train CAPEX", formula="CAPEX = sum(installed cost of selected utility-train items)", result=f"{utility_train_installed_capex:.2f}", units="INR"),
            CalcTrace(trace_id="transport_penalty_utility_basis", title="Transport-limited utility penalties", formula="Penalty utilities = absorber hydraulic electricity + solids auxiliaries + dryer endpoint steam", substitutions={"steam_load": f"{steam_load:.2f}", "power_load": f"{power_load:.2f}"}, result=f"{utility_cost:.2f}", units="INR/y"),
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
        scenario_results=scenario_results,
        integration_capex_inr=utility_train_installed_capex,
        equipment_cost_items=equipment_cost_items,
        value_records=[
            make_value_record("cost_total_capex", "Total CAPEX", total_capex, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_annual_opex", "Annual OPEX", annual_opex, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("cost_logistics_penalty", "Logistics penalty factor", logistics_penalty, "fraction", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_transport_service_penalty", "Annual transport/service penalty cost", transport_service_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_packing_replacement", "Annual packing replacement cost", annual_packing_replacement_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_filter_media_replacement", "Annual filter media replacement cost", annual_filter_media_replacement_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("cost_dryer_exhaust_treatment", "Annual dryer exhaust treatment cost", annual_dryer_exhaust_treatment_cost, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=citations,
        assumptions=assumptions
        + procurement_basis.assumptions
        + logistics_basis.assumptions
        + (["Cost model includes installed equipment implied by the selected utility exchanger train."] if utility_train_items else [])
        + ["Economics v2 ties CAPEX and OPEX to the selected procurement and logistics basis."],
    )


def build_working_capital_model_v2(
    basis: ProjectBasis,
    cost_model: CostModel,
    market_price_per_kg: float,
    citations: list[str],
    assumptions: list[str],
) -> WorkingCapitalModel:
    revenue = _annual_output_kg(basis) * market_price_per_kg
    raw_material_days = 18.0
    product_inventory_days = 10.0
    receivable_days = 32.0
    payable_days = 24.0
    working_capital = (
        cost_model.annual_raw_material_cost * raw_material_days / 365.0
        + revenue * product_inventory_days / 365.0
        + revenue * receivable_days / 365.0
        + cost_model.annual_opex * 8.0 / 365.0
        - cost_model.annual_raw_material_cost * payable_days / 365.0
    )
    return WorkingCapitalModel(
        raw_material_days=raw_material_days,
        product_inventory_days=product_inventory_days,
        receivable_days=receivable_days,
        payable_days=payable_days,
        working_capital_inr=round(working_capital, 2),
        calc_traces=[CalcTrace(trace_id="wc", title="Working capital", formula="WC = inventory + receivables + cash buffer - payables", result=f"{working_capital:.2f}", units="INR")],
        value_records=[make_value_record("wc_working_capital", "Working capital", working_capital, "INR", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH)],
        citations=citations,
        assumptions=assumptions + ["Working-capital model v2 uses an India manufacturing cash-cycle basis."],
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
    interest_rate = {"debt_equity_70_30": 0.105, "debt_equity_60_40": 0.11, "conservative_50_50": 0.12}.get(financing_basis.selected_candidate_id or "", 0.11)
    debt_fraction = {"debt_equity_70_30": 0.70, "debt_equity_60_40": 0.60, "conservative_50_50": 0.50}.get(financing_basis.selected_candidate_id or "", 0.60)
    total_investment = cost_model.total_capex + working_capital.working_capital_inr
    break_even_fraction = min(max(cost_model.annual_opex / max(annual_revenue, 1.0), 0.0), 1.5)
    annual_schedule: list[dict[str, float | str]] = []
    opening_debt = cost_model.total_capex * debt_fraction
    capacity_profile = [0.80, 0.85] + [0.90] * 10
    base_maintenance_cost = max(cost_model.annual_maintenance_cost - cost_model.annual_transport_service_cost, 0.0)
    packing_cycle_year = max(int(round(cost_model.packing_replacement_cycle_years)), 0)
    turnaround_cycle_year = max(cost_model.maintenance_turnaround_cycle_years, 0)
    minor_outage_days = cost_model.planned_minor_outage_days_per_year
    major_turnaround_days_basis = cost_model.planned_major_turnaround_days
    startup_loss_days_basis = cost_model.startup_loss_days_after_turnaround
    annual_operating_days = basis.annual_operating_days
    discount_rate = 0.12
    discounted_operating_cashflows = 0.0
    cumulative_cash = -total_investment
    payback_years: float | None = None
    last_year_cash = 1.0
    for year_index, utilization in enumerate(capacity_profile, start=1):
        turnaround_due = turnaround_cycle_year > 0 and year_index % turnaround_cycle_year == 0
        packing_due = packing_cycle_year > 0 and year_index % packing_cycle_year == 0
        year_major_turnaround_days = major_turnaround_days_basis if turnaround_due else 0.0
        year_startup_loss_days = startup_loss_days_basis if turnaround_due else 0.0
        available_operating_days = max(
            annual_operating_days - minor_outage_days - year_major_turnaround_days - year_startup_loss_days,
            annual_operating_days * 0.70,
        )
        availability_fraction = available_operating_days / max(annual_operating_days, 1.0)
        effective_utilization = max(utilization * availability_fraction, 0.65)
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
        year_packing_replacement = cost_model.packing_replacement_event_cost if packing_due else 0.0
        year_turnaround = cost_model.maintenance_turnaround_event_cost if turnaround_due else 0.0
        year_transport_service = (
            year_packing_replacement
            + year_classifier_service
            + year_filter_media
            + year_dryer_exhaust
        )
        year_maintenance_total = year_base_maintenance + year_transport_service + year_turnaround
        year_overheads = 0.19 * (year_labor + year_maintenance_total)
        year_opex = year_raw_material + year_utility + year_labor + year_maintenance_total + year_overheads
        year_depreciation = depreciation
        year_interest = max(opening_debt, 0.0) * interest_rate
        year_pbt = year_revenue - year_opex - year_depreciation - year_interest
        year_tax = max(year_pbt, 0.0) * 0.25
        year_pat = year_pbt - year_tax
        year_cash = year_pat + year_depreciation
        last_year_cash = max(year_cash, 1.0)
        discounted_operating_cashflows += year_cash / ((1.0 + discount_rate) ** year_index)
        if payback_years is None:
            previous_cumulative_cash = cumulative_cash
            cumulative_cash += year_cash
            if cumulative_cash >= 0.0:
                payback_years = (year_index - 1) + abs(previous_cumulative_cash) / max(year_cash, 1.0)
        else:
            cumulative_cash += year_cash
        principal_repayment = opening_debt * 0.12
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
                "revenue_inr": round(year_revenue, 2),
                "raw_material_cost_inr": round(year_raw_material, 2),
                "utility_cost_inr": round(year_utility, 2),
                "labor_cost_inr": round(year_labor, 2),
                "base_maintenance_inr": round(year_base_maintenance, 2),
                "transport_service_cost_inr": round(year_transport_service, 2),
                "packing_replacement_cost_inr": round(year_packing_replacement, 2),
                "classifier_service_cost_inr": round(year_classifier_service, 2),
                "filter_media_replacement_cost_inr": round(year_filter_media, 2),
                "dryer_exhaust_treatment_cost_inr": round(year_dryer_exhaust, 2),
                "turnaround_cost_inr": round(year_turnaround, 2),
                "turnaround_flag": "yes" if turnaround_due else "no",
                "operating_cost_inr": round(year_opex, 2),
                "interest_inr": round(year_interest, 2),
                "depreciation_inr": round(year_depreciation, 2),
                "profit_before_tax_inr": round(year_pbt, 2),
                "tax_inr": round(year_tax, 2),
                "profit_after_tax_inr": round(year_pat, 2),
                "cash_accrual_inr": round(year_cash, 2),
            }
        )
        opening_debt = max(opening_debt - principal_repayment, 0.0)
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
    return FinancialModel(
        currency=basis.currency,
        annual_revenue=round(annual_revenue, 2),
        annual_operating_cost=round(cost_model.annual_opex, 2),
        gross_profit=round(annual_revenue - cost_model.annual_opex, 2),
        working_capital=round(working_capital.working_capital_inr, 2),
        payback_years=round(payback_years, 3),
        npv=round(npv, 2),
        irr=round(irr, 2),
        profitability_index=round(profitability_index, 3),
        break_even_fraction=round(break_even_fraction, 3),
        annual_schedule=annual_schedule,
        calc_traces=[
            CalcTrace(trace_id="financial_cashflow", title="Annual cashflow", formula="Cashflow = PBT - tax + depreciation", result=f"{annual_cashflow:.2f}", units="INR/y"),
            CalcTrace(trace_id="financial_payback", title="Payback", formula="Payback uses cumulative yearwise cash accrual including replacement and turnaround events", result=f"{payback_years:.3f}", units="y"),
            CalcTrace(trace_id="financial_turnaround_schedule", title="Recurring maintenance timing basis", formula="Yearwise OPEX includes discrete packing replacement and turnaround events instead of a flat annualized maintenance burden", substitutions={"packing_cycle_years": f"{cost_model.packing_replacement_cycle_years:.2f}", "turnaround_cycle_years": str(cost_model.maintenance_turnaround_cycle_years)}, result=f"{cost_model.maintenance_turnaround_event_cost:.2f}", units="INR event"),
        ],
        scenario_results=cost_model.scenario_results,
        value_records=[
            make_value_record("financial_revenue", "Annual revenue", annual_revenue, "INR/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_payback", "Payback", payback_years, "y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("financial_irr", "IRR", irr, "%", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + financing_basis.assumptions + ["Financial model v2 includes depreciation, interest, and tax screening."],
    )


def build_economic_scenario_model_v2(
    cost_model: CostModel,
    financial_model: FinancialModel,
    economic_basis: DecisionRecord,
) -> EconomicScenarioModel:
    rows = [
        f"| {scenario.scenario_name} | {scenario.annual_revenue_inr:,.2f} | {scenario.annual_transport_service_cost_inr:,.2f} | {scenario.annual_operating_cost_inr:,.2f} | {scenario.gross_margin_inr:,.2f} |"
        for scenario in financial_model.scenario_results
    ]
    markdown = "\n".join(
        [
            "| Scenario | Revenue (INR/y) | Transport/Service (INR/y) | Opex (INR/y) | Gross Margin (INR/y) |",
            "| --- | --- | --- | --- | --- |",
            *rows,
        ]
    )
    if any(scenario.annual_transport_service_cost_inr > 0.0 for scenario in financial_model.scenario_results):
        breakdown_rows = [
            f"| {scenario.scenario_name} | {scenario.annual_packing_replacement_cost_inr:,.2f} | {scenario.annual_classifier_service_cost_inr:,.2f} | {scenario.annual_filter_media_replacement_cost_inr:,.2f} | {scenario.annual_dryer_exhaust_treatment_cost_inr:,.2f} |"
            for scenario in financial_model.scenario_results
        ]
        markdown += "\n\n" + "\n".join(
            [
                "| Scenario | Packing (INR/y) | Classifier (INR/y) | Filter Media (INR/y) | Dryer Exhaust (INR/y) |",
                "| --- | --- | --- | --- | --- |",
                *breakdown_rows,
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
    interest_rate = {"debt_equity_70_30": 0.105, "debt_equity_60_40": 0.11, "conservative_50_50": 0.12}.get(financing_basis.selected_candidate_id or "", 0.11)
    debt_fraction = {"debt_equity_70_30": 0.70, "debt_equity_60_40": 0.60, "conservative_50_50": 0.50}.get(financing_basis.selected_candidate_id or "", 0.60)
    opening_debt = cost_model.total_capex * debt_fraction
    principal_fraction = 1.0 / max(years, 1)
    entries: list[DebtScheduleEntry] = []
    for year in range(1, years + 1):
        principal = opening_debt * principal_fraction
        interest = opening_debt * interest_rate
        closing = max(opening_debt - principal, 0.0)
        entries.append(
            DebtScheduleEntry(
                year=year,
                opening_debt_inr=round(opening_debt, 2),
                principal_repayment_inr=round(principal, 2),
                interest_inr=round(interest, 2),
                closing_debt_inr=round(closing, 2),
                citations=cost_model.citations + financing_basis.citations,
                assumptions=cost_model.assumptions + financing_basis.assumptions,
            )
        )
        opening_debt = closing
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
            revenue_inr=float(row["revenue_inr"]),
            operating_cost_inr=float(row["operating_cost_inr"]),
            raw_material_cost_inr=float(row.get("raw_material_cost_inr", 0.0)),
            utility_cost_inr=float(row.get("utility_cost_inr", 0.0)),
            labor_cost_inr=float(row.get("labor_cost_inr", 0.0)),
            base_maintenance_inr=float(row.get("base_maintenance_inr", 0.0)),
            transport_service_cost_inr=float(row.get("transport_service_cost_inr", 0.0)),
            packing_replacement_cost_inr=float(row.get("packing_replacement_cost_inr", 0.0)),
            classifier_service_cost_inr=float(row.get("classifier_service_cost_inr", 0.0)),
            filter_media_replacement_cost_inr=float(row.get("filter_media_replacement_cost_inr", 0.0)),
            dryer_exhaust_treatment_cost_inr=float(row.get("dryer_exhaust_treatment_cost_inr", 0.0)),
            turnaround_cost_inr=float(row.get("turnaround_cost_inr", 0.0)),
            turnaround_flag=str(row.get("turnaround_flag", "no")).lower() == "yes",
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
            "| Year | Utilization (%) | Availability (%) | Minor Outage (d) | Turnaround (d) | Startup Loss (d) | Available Days | Revenue | Opex | Transport/Service | Packing | Turnaround Cost | Depreciation | Interest | PBT | Tax | PAT | Cash Accrual |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {line.year} | {line.capacity_utilization_pct:.2f} | {line.availability_pct:.2f} | {line.minor_outage_days:.2f} | {line.major_turnaround_days:.2f} | {line.startup_loss_days:.2f} | {line.available_operating_days:.2f} | {line.revenue_inr:,.2f} | {line.operating_cost_inr:,.2f} | {line.transport_service_cost_inr:,.2f} | {line.packing_replacement_cost_inr:,.2f} | {line.turnaround_cost_inr:,.2f} | {line.depreciation_inr:,.2f} | {line.interest_inr:,.2f} | {line.profit_before_tax_inr:,.2f} | {line.tax_inr:,.2f} | {line.profit_after_tax_inr:,.2f} | {line.cash_accrual_inr:,.2f} |"
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
