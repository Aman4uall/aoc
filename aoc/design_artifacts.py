from __future__ import annotations

from aoc.models import (
    ColumnDesign,
    ColumnHydraulics,
    EquipmentDatasheet,
    EquipmentListArtifact,
    EquipmentSpec,
    HeatExchangerDesign,
    HeatExchangerThermalDesign,
    MechanicalDesignArtifact,
    MechanicalDesignBasis,
    PumpDesign,
    ReactorDesign,
    ReactorDesignBasis,
    StorageDesign,
    VesselMechanicalDesign,
)


def build_reactor_design_basis(reactor: ReactorDesign) -> ReactorDesignBasis:
    return ReactorDesignBasis(
        reactor_id=reactor.reactor_id,
        selected_reactor_type=reactor.reactor_type,
        governing_equations=[
            "V = tau * volumetric_flow",
            "k = A * exp(-Ea/RT)",
            "Da = k * tau",
            "Q = U * A * LMTD",
            "Nu = 0.023 * Re^0.8 * Pr^0.4",
        ],
        design_inputs={
            "residence_time_hr": f"{reactor.residence_time_hr:.3f}",
            "design_volume_m3": f"{reactor.design_volume_m3:.3f}",
            "design_conversion_fraction": f"{reactor.design_conversion_fraction:.4f}",
            "phase_regime": reactor.phase_regime or "unspecified",
            "kinetic_rate_constant_1_hr": f"{reactor.kinetic_rate_constant_1_hr:.4f}",
            "kinetic_space_time_hr": f"{reactor.kinetic_space_time_hr:.4f}",
            "kinetic_damkohler_number": f"{reactor.kinetic_damkohler_number:.4f}",
            "heat_duty_kw": f"{reactor.heat_duty_kw:.3f}",
            "heat_release_density_kw_m3": f"{reactor.heat_release_density_kw_m3:.3f}",
            "adiabatic_temperature_rise_c": f"{reactor.adiabatic_temperature_rise_c:.3f}",
            "heat_removal_capacity_kw": f"{reactor.heat_removal_capacity_kw:.3f}",
            "heat_removal_margin_fraction": f"{reactor.heat_removal_margin_fraction:.4f}",
            "thermal_stability_score": f"{reactor.thermal_stability_score:.2f}",
            "runaway_risk_label": reactor.runaway_risk_label or "n/a",
            "integrated_thermal_duty_kw": f"{reactor.integrated_thermal_duty_kw:.3f}",
            "residual_utility_duty_kw": f"{reactor.residual_utility_duty_kw:.3f}",
            "integrated_lmtd_k": f"{reactor.integrated_lmtd_k:.3f}",
            "integrated_exchange_area_m2": f"{reactor.integrated_exchange_area_m2:.3f}",
            "allocated_recovered_duty_target_kw": f"{reactor.allocated_recovered_duty_target_kw:.3f}",
        },
        operating_envelope={
            "temperature_c": f"{reactor.design_temperature_c:.1f}",
            "pressure_bar": f"{reactor.design_pressure_bar:.2f}",
            "cooling_medium": reactor.cooling_medium,
            "utility_topology": reactor.utility_topology or "standalone utility service",
            "utility_architecture_family": reactor.utility_architecture_family or "base",
            "coupled_service_basis": reactor.coupled_service_basis or "none",
            "selected_utility_islands": ", ".join(reactor.selected_utility_island_ids) or "none",
            "selected_header_levels": ", ".join(str(level) for level in reactor.selected_utility_header_levels) or "none",
            "selected_cluster_ids": ", ".join(reactor.selected_utility_cluster_ids) or "none",
            "catalyst_name": reactor.catalyst_name or "none",
            "catalyst_inventory_kg": f"{reactor.catalyst_inventory_kg:.3f}",
            "catalyst_cycle_days": f"{reactor.catalyst_cycle_days:.1f}",
            "catalyst_regeneration_days": f"{reactor.catalyst_regeneration_days:.1f}",
            "catalyst_whsv_1_hr": f"{reactor.catalyst_weight_hourly_space_velocity_1_hr:.4f}",
        },
        markdown=(
            f"Reactor {reactor.reactor_id} uses {reactor.reactor_type} basis in {reactor.phase_regime or 'screening'} service with "
            f"k={reactor.kinetic_rate_constant_1_hr:.4f} 1/h and Da={reactor.kinetic_damkohler_number:.3f}. "
            f"Thermal stability basis gives DeltaTad={reactor.adiabatic_temperature_rise_c:.2f} C and heat-removal margin "
            f"{reactor.heat_removal_margin_fraction:.3f}. Integrated duty basis is {reactor.integrated_thermal_duty_kw:.3f} kW via "
            f"{reactor.utility_topology or 'standalone utilities'} [{reactor.utility_architecture_family or 'base'}], with explicit coupled area {reactor.integrated_exchange_area_m2:.3f} m2 at "
            f"{reactor.integrated_lmtd_k:.3f} K."
        ),
        citations=reactor.citations,
        assumptions=reactor.assumptions,
    )


def build_column_hydraulics(column: ColumnDesign) -> ColumnHydraulics:
    vapor_velocity = column.superficial_vapor_velocity_m_s or max(column.column_diameter_m, 0.1) * 0.85
    liquid_load = column.liquid_load_m3_hr or max(column.reboiler_duty_kw / 220.0, 1.0)
    active_area = max(
        (3.14159 * (column.column_diameter_m / 2.0) ** 2) * max(1.0 - column.downcomer_area_fraction, 0.25),
        0.1,
    )
    return ColumnHydraulics(
        column_id=column.column_id,
        flooding_fraction=column.flooding_fraction,
        tray_spacing_m=column.tray_spacing_m,
        downcomer_area_fraction=column.downcomer_area_fraction,
        vapor_velocity_m_s=round(vapor_velocity, 3),
        liquid_load_m3_hr=round(liquid_load, 3),
        capacity_factor_m_s=round(
            max(
                column.allowable_vapor_velocity_m_s
                / max((max((column.liquid_density_kg_m3 - column.vapor_density_kg_m3) / max(column.vapor_density_kg_m3, 0.05), 0.0) ** 0.5), 1e-6),
                0.0,
            ),
            3,
        ),
        allowable_vapor_velocity_m_s=round(column.allowable_vapor_velocity_m_s, 3),
        active_area_m2=round(active_area, 3),
        pressure_drop_per_stage_kpa=round(column.pressure_drop_per_stage_kpa, 3),
        markdown=(
            f"Column {column.column_id} hydraulic basis uses tray spacing {column.tray_spacing_m:.3f} m "
            f"and flooding fraction {column.flooding_fraction:.3f}, with superficial vapor velocity "
            f"{vapor_velocity:.3f} m/s against allowable {column.allowable_vapor_velocity_m_s:.3f} m/s. "
            f"Integrated reboiler duty basis is {column.integrated_reboiler_duty_kw:.3f} kW via {column.utility_topology or 'standalone utilities'}, "
            f"family {column.utility_architecture_family or 'base'}, with reboiler area {column.integrated_reboiler_area_m2:.3f} m2 at {column.integrated_reboiler_lmtd_k:.3f} K."
        ),
        citations=column.citations,
        assumptions=column.assumptions,
    )


def build_heat_exchanger_thermal_design(exchanger: HeatExchangerDesign) -> HeatExchangerThermalDesign:
    return HeatExchangerThermalDesign(
        exchanger_id=exchanger.exchanger_id,
        selected_configuration=exchanger.exchanger_type or "shell_and_tube",
        governing_equations=[
            "Q = U * A * LMTD",
            "A = Q / (U * LMTD)",
            "m_phase = Q / lambda",
        ],
        thermal_inputs={
            "heat_load_kw": f"{exchanger.heat_load_kw:.3f}",
            "lmtd_k": f"{exchanger.lmtd_k:.3f}",
            "u_w_m2_k": f"{exchanger.overall_u_w_m2_k:.3f}",
            "package_family": exchanger.package_family or "generic",
            "circulation_flow_m3_hr": f"{exchanger.circulation_flow_m3_hr:.3f}",
            "phase_change_load_kg_hr": f"{exchanger.phase_change_load_kg_hr:.3f}",
            "package_holdup_m3": f"{exchanger.package_holdup_m3:.3f}",
            "utility_topology": exchanger.utility_topology or "standalone utilities",
            "utility_architecture_family": exchanger.utility_architecture_family or "base",
            "selected_train_step_id": exchanger.selected_train_step_id or "none",
            "selected_island_id": exchanger.selected_island_id or "none",
            "selected_header_level": str(exchanger.selected_header_level or 0),
            "selected_cluster_id": exchanger.selected_cluster_id or "none",
            "allocated_recovered_duty_target_kw": f"{exchanger.allocated_recovered_duty_target_kw:.3f}",
            "boiling_side_coefficient_w_m2_k": f"{exchanger.boiling_side_coefficient_w_m2_k:.3f}",
            "condensing_side_coefficient_w_m2_k": f"{exchanger.condensing_side_coefficient_w_m2_k:.3f}",
        },
        package_basis={
            "package_family": exchanger.package_family or "generic",
            "selected_package_roles": ", ".join(exchanger.selected_package_roles) or "none",
            "selected_package_items": ", ".join(exchanger.selected_package_item_ids) or "none",
        },
        markdown=(
            f"Exchanger {exchanger.exchanger_id} uses {exchanger.exchanger_type or 'shell-and-tube'} "
            f"configuration with area {exchanger.area_m2:.3f} m2. "
            f"Selected utility-train step: {exchanger.selected_train_step_id or 'none'}; "
            f"package family: {exchanger.package_family or 'generic'}; "
            f"architecture family: {exchanger.utility_architecture_family or 'base'}."
        ),
        citations=exchanger.citations,
        assumptions=exchanger.assumptions,
    )


def build_pump_design(storage: StorageDesign, representative_equipment: EquipmentSpec | None = None) -> PumpDesign:
    design_flow = max(storage.working_volume_m3 / 8.0, 1.0)
    differential_head = 38.0 if representative_equipment and "storage" in representative_equipment.equipment_type.lower() else 52.0
    power_kw = design_flow * differential_head * 0.0032
    return PumpDesign(
        pump_id=f"{storage.storage_id}_pump",
        service=f"{storage.service} transfer",
        flow_m3_hr=round(design_flow, 3),
        differential_head_m=round(differential_head, 3),
        power_kw=round(power_kw, 3),
        npsh_margin_m=2.5,
        markdown=f"Screening product-transfer pump sized at {design_flow:.3f} m3/h and {differential_head:.1f} m head.",
        citations=storage.citations,
        assumptions=storage.assumptions,
    )


def build_equipment_datasheets(
    equipment_list: EquipmentListArtifact,
    reactor: ReactorDesign,
    column: ColumnDesign,
    exchanger: HeatExchangerDesign,
    storage: StorageDesign,
    mechanical_design: MechanicalDesignArtifact | None = None,
    vessel_designs: list[VesselMechanicalDesign] | None = None,
    mechanical_basis: MechanicalDesignBasis | None = None,
) -> list[EquipmentDatasheet]:
    datasheets: list[EquipmentDatasheet] = []
    equipment_map = {item.equipment_id: item for item in equipment_list.items}
    mechanical_index = {item.equipment_id: item for item in (mechanical_design.items if mechanical_design else [])}
    vessel_index = {item.equipment_id: item for item in (vessel_designs or [])}

    def _datasheet_markdown(equipment: EquipmentSpec, design_data: dict[str, str], notes: list[str]) -> str:
        rows = [f"- `{key}`: {value}" for key, value in design_data.items()]
        note_rows = [f"- {note}" for note in notes] or ["- none"]
        return "\n".join(
            [
                f"### {equipment.equipment_id} Datasheet",
                "",
                f"Service: {equipment.service}",
                "",
                "### Design Data",
                *rows,
                "",
                "### Notes",
                *note_rows,
            ]
        )

    for equipment in equipment_list.items:
        design_data = {
            "design_temperature_c": f"{equipment.design_temperature_c:.1f}",
            "design_pressure_bar": f"{equipment.design_pressure_bar:.2f}",
            "volume_m3": f"{equipment.volume_m3:.3f}",
            "material_of_construction": equipment.material_of_construction,
        }
        if equipment.equipment_id == reactor.reactor_id:
            design_data["phase_regime"] = reactor.phase_regime or "n/a"
            design_data["design_conversion_fraction"] = f"{reactor.design_conversion_fraction:.4f}"
            design_data["kinetic_rate_constant_1_hr"] = f"{reactor.kinetic_rate_constant_1_hr:.4f}"
            design_data["kinetic_space_time_hr"] = f"{reactor.kinetic_space_time_hr:.4f}"
            design_data["kinetic_damkohler_number"] = f"{reactor.kinetic_damkohler_number:.4f}"
            design_data["heat_release_density_kw_m3"] = f"{reactor.heat_release_density_kw_m3:.3f}"
            design_data["adiabatic_temperature_rise_c"] = f"{reactor.adiabatic_temperature_rise_c:.3f}"
            design_data["heat_removal_capacity_kw"] = f"{reactor.heat_removal_capacity_kw:.3f}"
            design_data["heat_removal_margin_fraction"] = f"{reactor.heat_removal_margin_fraction:.4f}"
            design_data["thermal_stability_score"] = f"{reactor.thermal_stability_score:.2f}"
            design_data["runaway_risk_label"] = reactor.runaway_risk_label or "n/a"
            design_data["catalyst_name"] = reactor.catalyst_name or "none"
            design_data["catalyst_inventory_kg"] = f"{reactor.catalyst_inventory_kg:.3f}"
            design_data["catalyst_cycle_days"] = f"{reactor.catalyst_cycle_days:.1f}"
            design_data["catalyst_regeneration_days"] = f"{reactor.catalyst_regeneration_days:.1f}"
            design_data["catalyst_whsv_1_hr"] = f"{reactor.catalyst_weight_hourly_space_velocity_1_hr:.4f}"
            design_data["heat_transfer_area_m2"] = f"{reactor.heat_transfer_area_m2:.3f}"
            design_data["integrated_thermal_duty_kw"] = f"{reactor.integrated_thermal_duty_kw:.3f}"
            design_data["integrated_exchange_area_m2"] = f"{reactor.integrated_exchange_area_m2:.3f}"
            design_data["reactor_utility_topology"] = reactor.utility_topology or "standalone"
            design_data["reactor_utility_architecture_family"] = reactor.utility_architecture_family or "base"
            design_data["reactor_selected_utility_islands"] = ", ".join(reactor.selected_utility_island_ids) or "none"
        if equipment.equipment_id == column.column_id:
            design_data["design_stages"] = str(column.design_stages)
            design_data["theoretical_stages"] = f"{column.theoretical_stages:.3f}"
            design_data["minimum_reflux_ratio"] = f"{column.minimum_reflux_ratio:.3f}"
            design_data["reflux_ratio"] = f"{column.reflux_ratio:.3f}"
            design_data["tray_efficiency"] = f"{column.tray_efficiency:.3f}"
            design_data["feed_quality_q_factor"] = f"{column.feed_quality_q_factor:.3f}"
            design_data["murphree_efficiency"] = f"{column.murphree_efficiency:.3f}"
            design_data["top_relative_volatility"] = f"{column.top_relative_volatility:.3f}"
            design_data["bottom_relative_volatility"] = f"{column.bottom_relative_volatility:.3f}"
            design_data["rectifying_theoretical_stages"] = f"{column.rectifying_theoretical_stages:.3f}"
            design_data["stripping_theoretical_stages"] = f"{column.stripping_theoretical_stages:.3f}"
            design_data["rectifying_vapor_load_kg_hr"] = f"{column.rectifying_vapor_load_kg_hr:.3f}"
            design_data["stripping_vapor_load_kg_hr"] = f"{column.stripping_vapor_load_kg_hr:.3f}"
            design_data["rectifying_liquid_load_m3_hr"] = f"{column.rectifying_liquid_load_m3_hr:.3f}"
            design_data["stripping_liquid_load_m3_hr"] = f"{column.stripping_liquid_load_m3_hr:.3f}"
            design_data["integrated_reboiler_duty_kw"] = f"{column.integrated_reboiler_duty_kw:.3f}"
            design_data["integrated_reboiler_area_m2"] = f"{column.integrated_reboiler_area_m2:.3f}"
            design_data["allocated_reboiler_recovery_target_kw"] = f"{column.allocated_reboiler_recovery_target_kw:.3f}"
            design_data["allocated_condenser_recovery_target_kw"] = f"{column.allocated_condenser_recovery_target_kw:.3f}"
            design_data["reboiler_package_type"] = column.reboiler_package_type or "none"
            design_data["condenser_package_type"] = column.condenser_package_type or "none"
            design_data["column_utility_topology"] = column.utility_topology or "standalone"
            design_data["column_utility_architecture_family"] = column.utility_architecture_family or "base"
            design_data["column_selected_utility_islands"] = ", ".join(column.selected_utility_island_ids) or "none"
            design_data["equilibrium_model"] = column.equilibrium_model or "none"
            design_data["equilibrium_parameter_ids"] = ", ".join(column.equilibrium_parameter_ids) or "none"
            if column.absorber_key_component:
                design_data["absorber_key_component"] = column.absorber_key_component
                design_data["absorber_capture_fraction"] = f"{column.absorber_capture_fraction:.3f}"
                design_data["absorber_minimum_solvent_to_gas_ratio"] = f"{column.absorber_minimum_solvent_to_gas_ratio:.3f}"
                design_data["absorber_optimized_solvent_to_gas_ratio"] = f"{column.absorber_optimized_solvent_to_gas_ratio:.3f}"
                design_data["absorber_lean_loading_mol_mol"] = f"{column.absorber_lean_loading_mol_mol:.5f}"
                design_data["absorber_rich_loading_mol_mol"] = f"{column.absorber_rich_loading_mol_mol:.5f}"
                design_data["absorber_solvent_rate_case_count"] = str(column.absorber_solvent_rate_case_count)
                design_data["absorber_theoretical_stages"] = f"{column.absorber_theoretical_stages:.3f}"
                design_data["absorber_packed_height_m"] = f"{column.absorber_packed_height_m:.3f}"
                design_data["absorber_gas_mass_velocity_kg_m2_s"] = f"{column.absorber_gas_mass_velocity_kg_m2_s:.3f}"
                design_data["absorber_liquid_mass_velocity_kg_m2_s"] = f"{column.absorber_liquid_mass_velocity_kg_m2_s:.3f}"
                design_data["absorber_packing_family"] = column.absorber_packing_family or "none"
                design_data["absorber_packing_specific_area_m2_m3"] = f"{column.absorber_packing_specific_area_m2_m3:.3f}"
                design_data["absorber_effective_interfacial_area_m2_m3"] = f"{column.absorber_effective_interfacial_area_m2_m3:.3f}"
                design_data["absorber_gas_phase_transfer_coeff_1_s"] = f"{column.absorber_gas_phase_transfer_coeff_1_s:.3f}"
                design_data["absorber_liquid_phase_transfer_coeff_1_s"] = f"{column.absorber_liquid_phase_transfer_coeff_1_s:.3f}"
                design_data["absorber_ntu"] = f"{column.absorber_ntu:.3f}"
                design_data["absorber_htu_m"] = f"{column.absorber_htu_m:.3f}"
                design_data["absorber_overall_mass_transfer_coefficient_1_s"] = f"{column.absorber_overall_mass_transfer_coefficient_1_s:.3f}"
                design_data["absorber_min_wetting_rate_kg_m2_s"] = f"{column.absorber_min_wetting_rate_kg_m2_s:.3f}"
                design_data["absorber_wetting_ratio"] = f"{column.absorber_wetting_ratio:.3f}"
                design_data["absorber_operating_velocity_m_s"] = f"{column.absorber_operating_velocity_m_s:.3f}"
                design_data["absorber_flooding_velocity_m_s"] = f"{column.absorber_flooding_velocity_m_s:.3f}"
                design_data["absorber_flooding_margin_fraction"] = f"{column.absorber_flooding_margin_fraction:.3f}"
                design_data["absorber_pressure_drop_per_m_kpa_m"] = f"{column.absorber_pressure_drop_per_m_kpa_m:.3f}"
                design_data["absorber_total_pressure_drop_kpa"] = f"{column.absorber_total_pressure_drop_kpa:.3f}"
            if column.crystallizer_key_component:
                design_data["crystallizer_key_component"] = column.crystallizer_key_component
                design_data["crystallizer_yield_fraction"] = f"{column.crystallizer_yield_fraction:.3f}"
                design_data["crystallizer_residence_time_hr"] = f"{column.crystallizer_residence_time_hr:.3f}"
                design_data["crystallizer_holdup_m3"] = f"{column.crystallizer_holdup_m3:.3f}"
                design_data["crystal_slurry_density_kg_m3"] = f"{column.crystal_slurry_density_kg_m3:.3f}"
                design_data["crystal_growth_rate_mm_hr"] = f"{column.crystal_growth_rate_mm_hr:.3f}"
                design_data["crystal_size_d10_mm"] = f"{column.crystal_size_d10_mm:.3f}"
                design_data["crystal_size_d50_mm"] = f"{column.crystal_size_d50_mm:.3f}"
                design_data["crystal_size_d90_mm"] = f"{column.crystal_size_d90_mm:.3f}"
                design_data["crystal_classifier_cut_size_mm"] = f"{column.crystal_classifier_cut_size_mm:.3f}"
                design_data["crystal_classified_product_fraction"] = f"{column.crystal_classified_product_fraction:.3f}"
                design_data["slurry_circulation_rate_m3_hr"] = f"{column.slurry_circulation_rate_m3_hr:.3f}"
                design_data["filter_area_m2"] = f"{column.filter_area_m2:.3f}"
                design_data["filter_cake_throughput_kg_m2_hr"] = f"{column.filter_cake_throughput_kg_m2_hr:.3f}"
                design_data["filter_specific_cake_resistance_m_kg"] = f"{column.filter_specific_cake_resistance_m_kg:.3e}"
                design_data["filter_medium_resistance_1_m"] = f"{column.filter_medium_resistance_1_m:.3e}"
                design_data["filter_cycle_time_hr"] = f"{column.filter_cycle_time_hr:.3f}"
                design_data["filter_cake_formation_time_hr"] = f"{column.filter_cake_formation_time_hr:.3f}"
                design_data["filter_wash_time_hr"] = f"{column.filter_wash_time_hr:.3f}"
                design_data["filter_discharge_time_hr"] = f"{column.filter_discharge_time_hr:.3f}"
                design_data["filter_cycles_per_hr"] = f"{column.filter_cycles_per_hr:.3f}"
                design_data["dryer_evaporation_load_kg_hr"] = f"{column.dryer_evaporation_load_kg_hr:.3f}"
                design_data["dryer_residence_time_hr"] = f"{column.dryer_residence_time_hr:.3f}"
                design_data["dryer_target_moisture_fraction"] = f"{column.dryer_target_moisture_fraction:.3f}"
                design_data["dryer_product_moisture_fraction"] = f"{column.dryer_product_moisture_fraction:.3f}"
                design_data["dryer_equilibrium_moisture_fraction"] = f"{column.dryer_equilibrium_moisture_fraction:.3f}"
                design_data["dryer_endpoint_margin_fraction"] = f"{column.dryer_endpoint_margin_fraction:.3f}"
                design_data["dryer_inlet_humidity_ratio_kg_kg"] = f"{column.dryer_inlet_humidity_ratio_kg_kg:.3f}"
                design_data["dryer_exhaust_humidity_ratio_kg_kg"] = f"{column.dryer_exhaust_humidity_ratio_kg_kg:.3f}"
                design_data["dryer_humidity_lift_kg_kg"] = f"{column.dryer_humidity_lift_kg_kg:.3f}"
                design_data["dryer_exhaust_dewpoint_c"] = f"{column.dryer_exhaust_dewpoint_c:.3f}"
                design_data["dryer_dry_air_flow_kg_hr"] = f"{column.dryer_dry_air_flow_kg_hr:.3f}"
                design_data["dryer_exhaust_saturation_fraction"] = f"{column.dryer_exhaust_saturation_fraction:.3f}"
                design_data["dryer_mass_transfer_coefficient_kg_m2_s"] = f"{column.dryer_mass_transfer_coefficient_kg_m2_s:.5f}"
                design_data["dryer_heat_transfer_coefficient_w_m2_k"] = f"{column.dryer_heat_transfer_coefficient_w_m2_k:.3f}"
                design_data["dryer_heat_transfer_area_m2"] = f"{column.dryer_heat_transfer_area_m2:.3f}"
                design_data["dryer_refined_duty_kw"] = f"{column.dryer_refined_duty_kw:.3f}"
        if equipment.equipment_id == exchanger.exchanger_id:
            design_data["heat_load_kw"] = f"{exchanger.heat_load_kw:.3f}"
            design_data["area_m2"] = f"{exchanger.area_m2:.3f}"
            design_data["package_family"] = exchanger.package_family or "generic"
            design_data["circulation_flow_m3_hr"] = f"{exchanger.circulation_flow_m3_hr:.3f}"
            design_data["phase_change_load_kg_hr"] = f"{exchanger.phase_change_load_kg_hr:.3f}"
            design_data["boiling_side_coefficient_w_m2_k"] = f"{exchanger.boiling_side_coefficient_w_m2_k:.3f}"
            design_data["condensing_side_coefficient_w_m2_k"] = f"{exchanger.condensing_side_coefficient_w_m2_k:.3f}"
            design_data["selected_package_roles"] = ", ".join(exchanger.selected_package_roles) or "none"
            design_data["selected_train_step_id"] = exchanger.selected_train_step_id or "none"
        if equipment.equipment_id == storage.storage_id:
            design_data["inventory_days"] = f"{storage.inventory_days:.1f}"
            design_data["total_volume_m3"] = f"{storage.total_volume_m3:.3f}"
        mechanical_item = mechanical_index.get(equipment.equipment_id)
        vessel_item = vessel_index.get(equipment.equipment_id)
        notes = [equipment.notes] if equipment.notes else []
        if mechanical_item:
            design_data["pressure_class"] = mechanical_item.pressure_class or "n/a"
            design_data["hydrotest_pressure_bar"] = f"{mechanical_item.hydrotest_pressure_bar:.3f}"
            design_data["support_type"] = mechanical_item.support_type
            design_data["support_variant"] = mechanical_item.support_variant or mechanical_item.support_type
            design_data["support_load_case"] = mechanical_item.support_load_case or "n/a"
            design_data["wind_load_kn"] = f"{mechanical_item.wind_load_kn:.3f}"
            design_data["seismic_load_kn"] = f"{mechanical_item.seismic_load_kn:.3f}"
            design_data["piping_load_kn"] = f"{mechanical_item.piping_load_kn:.3f}"
            design_data["foundation_footprint_m2"] = f"{mechanical_item.foundation_footprint_m2:.3f}"
            design_data["maintenance_clearance_m"] = f"{mechanical_item.maintenance_clearance_m:.3f}"
            design_data["platform_required"] = "yes" if mechanical_item.maintenance_platform_required else "no"
            design_data["platform_area_m2"] = f"{mechanical_item.platform_area_m2:.3f}"
            design_data["access_ladder_required"] = "yes" if mechanical_item.access_ladder_required else "no"
            design_data["lifting_lug_required"] = "yes" if mechanical_item.lifting_lug_required else "no"
            design_data["anchor_group_count"] = str(mechanical_item.anchor_group_count)
            design_data["nozzle_reinforcement_family"] = mechanical_item.nozzle_reinforcement_family or "n/a"
            design_data["local_shell_load_interaction_factor"] = f"{mechanical_item.local_shell_load_interaction_factor:.3f}"
            notes.append(
                f"Mechanical basis uses {mechanical_item.support_variant or mechanical_item.support_type} support with "
                f"{mechanical_item.nozzle_reinforcement_family or 'screening'} nozzle reinforcement."
            )
        if vessel_item:
            design_data["nozzle_services"] = ", ".join(vessel_item.nozzle_schedule.nozzle_services) or "none"
            design_data["nozzle_connection_classes"] = ", ".join(vessel_item.nozzle_schedule.nozzle_connection_classes) or "none"
            design_data["nozzle_orientations_deg"] = ", ".join(
                f"{value:.0f}" for value in vessel_item.nozzle_schedule.nozzle_orientations_deg
            ) or "none"
            design_data["nozzle_projection_mm"] = ", ".join(
                f"{value:.1f}" for value in vessel_item.nozzle_schedule.nozzle_projection_mm
            ) or "none"
            design_data["local_shell_load_factors"] = ", ".join(
                f"{value:.3f}" for value in vessel_item.nozzle_schedule.local_shell_load_factors
            ) or "none"
        if mechanical_basis:
            design_data["mechanical_code_basis"] = mechanical_basis.code_basis
            design_data["foundation_basis"] = mechanical_basis.foundation_basis or mechanical_basis.support_design_basis
            design_data["nozzle_load_basis"] = mechanical_basis.nozzle_load_basis or mechanical_basis.load_case_basis
        datasheets.append(
            EquipmentDatasheet(
                datasheet_id=f"{equipment.equipment_id}_datasheet",
                equipment_id=equipment.equipment_id,
                equipment_type=equipment.equipment_type,
                service=equipment.service,
                design_data=design_data,
                notes=notes,
                markdown=_datasheet_markdown(equipment, design_data, notes),
                citations=equipment.citations,
                assumptions=equipment.assumptions,
            )
        )
    for equipment in equipment_map.values():
        if not any(item.equipment_id == equipment.equipment_id for item in datasheets):
            fallback_design_data = {
                "design_temperature_c": f"{equipment.design_temperature_c:.1f}",
                "design_pressure_bar": f"{equipment.design_pressure_bar:.2f}",
                "volume_m3": f"{equipment.volume_m3:.3f}",
            }
            mechanical_item = mechanical_index.get(equipment.equipment_id)
            if mechanical_item:
                fallback_design_data["pressure_class"] = mechanical_item.pressure_class or "n/a"
                fallback_design_data["hydrotest_pressure_bar"] = f"{mechanical_item.hydrotest_pressure_bar:.3f}"
            datasheets.append(
                EquipmentDatasheet(
                    datasheet_id=f"{equipment.equipment_id}_datasheet",
                    equipment_id=equipment.equipment_id,
                    equipment_type=equipment.equipment_type,
                    service=equipment.service,
                    design_data=fallback_design_data,
                    markdown=_datasheet_markdown(equipment, fallback_design_data, [equipment.notes] if equipment.notes else []),
                    citations=equipment.citations,
                    assumptions=equipment.assumptions,
                )
            )
    return datasheets
