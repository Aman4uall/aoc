from __future__ import annotations

from aoc.models import (
    ColumnDesign,
    ColumnHydraulics,
    EquipmentDatasheet,
    EquipmentListArtifact,
    EquipmentSpec,
    HeatExchangerDesign,
    HeatExchangerThermalDesign,
    PumpDesign,
    ReactorDesign,
    ReactorDesignBasis,
    StorageDesign,
)


def build_reactor_design_basis(reactor: ReactorDesign) -> ReactorDesignBasis:
    return ReactorDesignBasis(
        reactor_id=reactor.reactor_id,
        selected_reactor_type=reactor.reactor_type,
        governing_equations=[
            "V = tau * volumetric_flow",
            "Q = U * A * LMTD",
            "Nu = 0.023 * Re^0.8 * Pr^0.4",
        ],
        design_inputs={
            "residence_time_hr": f"{reactor.residence_time_hr:.3f}",
            "design_volume_m3": f"{reactor.design_volume_m3:.3f}",
            "heat_duty_kw": f"{reactor.heat_duty_kw:.3f}",
            "integrated_thermal_duty_kw": f"{reactor.integrated_thermal_duty_kw:.3f}",
            "residual_utility_duty_kw": f"{reactor.residual_utility_duty_kw:.3f}",
            "integrated_lmtd_k": f"{reactor.integrated_lmtd_k:.3f}",
            "integrated_exchange_area_m2": f"{reactor.integrated_exchange_area_m2:.3f}",
        },
        operating_envelope={
            "temperature_c": f"{reactor.design_temperature_c:.1f}",
            "pressure_bar": f"{reactor.design_pressure_bar:.2f}",
            "cooling_medium": reactor.cooling_medium,
            "utility_topology": reactor.utility_topology or "standalone utility service",
            "coupled_service_basis": reactor.coupled_service_basis or "none",
        },
        markdown=(
            f"Reactor {reactor.reactor_id} uses {reactor.reactor_type} basis with U={reactor.overall_u_w_m2_k:.1f} W/m2-K. "
            f"Integrated duty basis is {reactor.integrated_thermal_duty_kw:.3f} kW via {reactor.utility_topology or 'standalone utilities'}, "
            f"with explicit coupled area {reactor.integrated_exchange_area_m2:.3f} m2 at {reactor.integrated_lmtd_k:.3f} K."
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
            f"with reboiler area {column.integrated_reboiler_area_m2:.3f} m2 at {column.integrated_reboiler_lmtd_k:.3f} K."
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
            "selected_train_step_id": exchanger.selected_train_step_id or "none",
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
            f"package family: {exchanger.package_family or 'generic'}."
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
) -> list[EquipmentDatasheet]:
    datasheets: list[EquipmentDatasheet] = []
    equipment_map = {item.equipment_id: item for item in equipment_list.items}
    for equipment in equipment_list.items:
        design_data = {
            "design_temperature_c": f"{equipment.design_temperature_c:.1f}",
            "design_pressure_bar": f"{equipment.design_pressure_bar:.2f}",
            "volume_m3": f"{equipment.volume_m3:.3f}",
            "material_of_construction": equipment.material_of_construction,
        }
        if equipment.equipment_id == reactor.reactor_id:
            design_data["heat_transfer_area_m2"] = f"{reactor.heat_transfer_area_m2:.3f}"
            design_data["integrated_thermal_duty_kw"] = f"{reactor.integrated_thermal_duty_kw:.3f}"
            design_data["integrated_exchange_area_m2"] = f"{reactor.integrated_exchange_area_m2:.3f}"
            design_data["reactor_utility_topology"] = reactor.utility_topology or "standalone"
        if equipment.equipment_id == column.column_id:
            design_data["design_stages"] = str(column.design_stages)
            design_data["theoretical_stages"] = f"{column.theoretical_stages:.3f}"
            design_data["minimum_reflux_ratio"] = f"{column.minimum_reflux_ratio:.3f}"
            design_data["reflux_ratio"] = f"{column.reflux_ratio:.3f}"
            design_data["tray_efficiency"] = f"{column.tray_efficiency:.3f}"
            design_data["integrated_reboiler_duty_kw"] = f"{column.integrated_reboiler_duty_kw:.3f}"
            design_data["integrated_reboiler_area_m2"] = f"{column.integrated_reboiler_area_m2:.3f}"
            design_data["reboiler_package_type"] = column.reboiler_package_type or "none"
            design_data["condenser_package_type"] = column.condenser_package_type or "none"
            design_data["column_utility_topology"] = column.utility_topology or "standalone"
            design_data["equilibrium_model"] = column.equilibrium_model or "none"
            design_data["equilibrium_parameter_ids"] = ", ".join(column.equilibrium_parameter_ids) or "none"
            if column.absorber_key_component:
                design_data["absorber_key_component"] = column.absorber_key_component
                design_data["absorber_capture_fraction"] = f"{column.absorber_capture_fraction:.3f}"
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
                design_data["dryer_evaporation_load_kg_hr"] = f"{column.dryer_evaporation_load_kg_hr:.3f}"
                design_data["dryer_residence_time_hr"] = f"{column.dryer_residence_time_hr:.3f}"
                design_data["dryer_target_moisture_fraction"] = f"{column.dryer_target_moisture_fraction:.3f}"
                design_data["dryer_product_moisture_fraction"] = f"{column.dryer_product_moisture_fraction:.3f}"
                design_data["dryer_equilibrium_moisture_fraction"] = f"{column.dryer_equilibrium_moisture_fraction:.3f}"
                design_data["dryer_inlet_humidity_ratio_kg_kg"] = f"{column.dryer_inlet_humidity_ratio_kg_kg:.3f}"
                design_data["dryer_exhaust_humidity_ratio_kg_kg"] = f"{column.dryer_exhaust_humidity_ratio_kg_kg:.3f}"
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
        datasheets.append(
            EquipmentDatasheet(
                datasheet_id=f"{equipment.equipment_id}_datasheet",
                equipment_id=equipment.equipment_id,
                equipment_type=equipment.equipment_type,
                service=equipment.service,
                design_data=design_data,
                notes=[equipment.notes] if equipment.notes else [],
                markdown=f"Datasheet for {equipment.equipment_id}: {equipment.service}.",
                citations=equipment.citations,
                assumptions=equipment.assumptions,
            )
        )
    for equipment in equipment_map.values():
        if not any(item.equipment_id == equipment.equipment_id for item in datasheets):
            datasheets.append(
                EquipmentDatasheet(
                    datasheet_id=f"{equipment.equipment_id}_datasheet",
                    equipment_id=equipment.equipment_id,
                    equipment_type=equipment.equipment_type,
                    service=equipment.service,
                    design_data={
                        "design_temperature_c": f"{equipment.design_temperature_c:.1f}",
                        "design_pressure_bar": f"{equipment.design_pressure_bar:.2f}",
                        "volume_m3": f"{equipment.volume_m3:.3f}",
                    },
                    markdown=f"Datasheet for {equipment.equipment_id}: {equipment.service}.",
                    citations=equipment.citations,
                    assumptions=equipment.assumptions,
                )
            )
    return datasheets
