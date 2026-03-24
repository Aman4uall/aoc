from __future__ import annotations

import math

from aoc.models import (
    CalcTrace,
    ColumnDesign,
    DecisionRecord,
    EnergyBalance,
    EquipmentSpec,
    HeatExchangerDesign,
    ProjectBasis,
    ReactionSystem,
    ReactorDesign,
    RouteOption,
    SensitivityLevel,
    StorageDesign,
    StreamTable,
)
from aoc.value_engine import make_value_record


def _feed_mass(stream_table: StreamTable) -> float:
    return sum(sum(component.mass_flow_kg_hr for component in stream.components) for stream in stream_table.streams if stream.stream_id.startswith("S-10"))


def _product_mass(stream_table: StreamTable) -> float:
    for stream in stream_table.streams:
        if "on-spec product" in stream.description.lower():
            return sum(component.mass_flow_kg_hr for component in stream.components)
    return sum(sum(component.mass_flow_kg_hr for component in stream.components) for stream in stream_table.streams if stream.stream_id == "S-401")


def _product_stream_id(stream_table: StreamTable) -> str:
    for stream in stream_table.streams:
        if "on-spec product" in stream.description.lower():
            return stream.stream_id
    return "S-401"


def _duty_for_prefix(energy_balance: EnergyBalance, prefixes: tuple[str, ...]) -> float:
    matches = [
        max(duty.heating_kw, duty.cooling_kw)
        for duty in energy_balance.duties
        if any(duty.unit_id.startswith(prefix) for prefix in prefixes)
    ]
    return max(matches) if matches else max(
        max(duty.heating_kw, duty.cooling_kw) for duty in energy_balance.duties
    )


def build_reactor_design_generic(
    basis: ProjectBasis,
    route: RouteOption,
    reaction_system: ReactionSystem,
    stream_table: StreamTable,
    energy_balance: EnergyBalance,
    reactor_choice: DecisionRecord | None = None,
) -> ReactorDesign:
    reactor_type = reactor_choice.selected_candidate_id if reactor_choice and reactor_choice.selected_candidate_id else "jacketed_cstr"
    feed_mass = _feed_mass(stream_table)
    density = 1150.0 if "solid" in reactor_type else 1020.0 if "aqueous" in reactor_type or "hydrator" in reactor_type else 900.0
    volumetric_flow_m3_hr = max(feed_mass / density, 0.1)
    residence_time = reaction_system.excess_ratio * 0.03 + route.residence_time_hr
    if "fixed_bed" in reactor_type or "converter" in reactor_type:
        liquid_holdup_m3 = volumetric_flow_m3_hr * residence_time * 0.65
        design_factor = 1.35
    elif "plug_flow" in reactor_type or "tubular" in reactor_type:
        liquid_holdup_m3 = volumetric_flow_m3_hr * residence_time
        design_factor = 1.18
    elif "batch" in reactor_type:
        liquid_holdup_m3 = volumetric_flow_m3_hr * residence_time * 1.8
        design_factor = 1.25
    else:
        liquid_holdup_m3 = volumetric_flow_m3_hr * residence_time * 1.15
        design_factor = 1.22
    design_volume = liquid_holdup_m3 * design_factor
    reactor_duty = _duty_for_prefix(energy_balance, ("R-", "CONV"))
    u_value = 850.0 if "plug_flow" in reactor_type or "hydrator" in reactor_type else 600.0
    lmtd = 24.0 if reactor_duty > 0 else 18.0
    area = max((reactor_duty * 1000.0) / max(u_value * lmtd, 1.0), 1.0)
    shell_diameter = max((4.0 * design_volume / (math.pi * 5.0)) ** (1.0 / 3.0), 1.1)
    shell_length = max(design_volume / (math.pi * (shell_diameter / 2.0) ** 2), 4.5)
    viscosity_pa_s = 0.0018 if "hydrator" in reactor_type else 0.0024
    hydraulic_diameter_m = 0.032 if "plug_flow" in reactor_type or "hydrator" in reactor_type else 0.055
    velocity_m_s = max((volumetric_flow_m3_hr / 3600.0) / max(math.pi * (shell_diameter / 2.0) ** 2 * 0.55, 1e-6), 0.2)
    reynolds = max((density * velocity_m_s * hydraulic_diameter_m) / max(viscosity_pa_s, 1e-6), 1000.0)
    prandtl = 12.0 if "hydrator" in reactor_type else 8.5
    nusselt = 0.023 * (reynolds ** 0.8) * (prandtl ** 0.4)
    tube_length = max(shell_length * 0.88, 4.0)
    tube_area = math.pi * 0.025 * tube_length
    tube_count = max(int(math.ceil(area / max(tube_area, 1e-6))), 24)
    traces = [
        CalcTrace(trace_id="reactor_holdup", title="Reactor holdup", formula="V = Qv * tau * factor", substitutions={"Qv": f"{volumetric_flow_m3_hr:.3f}", "tau": f"{residence_time:.3f}"}, result=f"{liquid_holdup_m3:.3f}", units="m3"),
        CalcTrace(trace_id="reactor_design_volume", title="Reactor design volume", formula="Vd = V * design_factor", substitutions={"V": f"{liquid_holdup_m3:.3f}", "factor": f"{design_factor:.3f}"}, result=f"{design_volume:.3f}", units="m3"),
        CalcTrace(trace_id="reactor_reynolds", title="Reactor-side Reynolds number", formula="Re = rho * v * Dh / mu", substitutions={"rho": f"{density:.1f}", "v": f"{velocity_m_s:.3f}", "Dh": f"{hydraulic_diameter_m:.3f}", "mu": f"{viscosity_pa_s:.5f}"}, result=f"{reynolds:.1f}", units="-"),
        CalcTrace(trace_id="reactor_nusselt", title="Reactor-side Nusselt number", formula="Nu = 0.023 Re^0.8 Pr^0.4", substitutions={"Re": f"{reynolds:.1f}", "Pr": f"{prandtl:.2f}"}, result=f"{nusselt:.2f}", units="-"),
    ]
    return ReactorDesign(
        reactor_id="R-101",
        reactor_type=reactor_type.replace("_", " ").title(),
        design_basis=f"{reactor_type} selected at {residence_time:.2f} h residence time and {reaction_system.conversion_fraction:.3f} conversion basis.",
        residence_time_hr=round(residence_time, 3),
        liquid_holdup_m3=round(liquid_holdup_m3, 3),
        design_volume_m3=round(design_volume, 3),
        design_temperature_c=round(route.operating_temperature_c + 15.0, 1),
        design_pressure_bar=round(max(route.operating_pressure_bar + 2.0, 2.5), 2),
        heat_duty_kw=round(reactor_duty, 3),
        heat_transfer_area_m2=round(area, 3),
        shell_diameter_m=round(shell_diameter, 3),
        shell_length_m=round(shell_length, 3),
        overall_u_w_m2_k=round(u_value, 3),
        reynolds_number=round(reynolds, 2),
        prandtl_number=round(prandtl, 3),
        nusselt_number=round(nusselt, 2),
        number_of_tubes=tube_count,
        tube_length_m=round(tube_length, 3),
        cooling_medium="Dowtherm / cooling water" if reactor_duty > 0 else "Steam / hot oil",
        calc_traces=traces,
        value_records=[
            make_value_record("reactor_design_volume", "Reactor design volume", design_volume, "m3", citations=route.citations, assumptions=route.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("reactor_heat_duty", "Reactor heat duty", reactor_duty, "kW", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=sorted(set(route.citations + reaction_system.citations + energy_balance.citations + (reactor_choice.citations if reactor_choice else []))),
        assumptions=route.assumptions + reaction_system.assumptions + energy_balance.assumptions + (reactor_choice.assumptions if reactor_choice else []),
    )


def build_column_design_generic(
    basis: ProjectBasis,
    route: RouteOption,
    stream_table: StreamTable,
    energy_balance: EnergyBalance,
    separation_choice: DecisionRecord | None = None,
) -> ColumnDesign:
    separation_type = separation_choice.selected_candidate_id if separation_choice and separation_choice.selected_candidate_id else "distillation_train"
    product_mass = _product_mass(stream_table)
    if "absorption" in separation_type:
        service = "Absorption tower train"
        light_key = "Offgas"
        heavy_key = "Rich absorbent"
        alpha = 1.08
        stages = 10
        reflux = 0.20
        diameter = max(math.sqrt(product_mass / 9000.0), 1.5)
        height = 18.0
        reboiler = max(energy_balance.total_heating_kw * 0.18, 1200.0)
        condenser = max(energy_balance.total_cooling_kw * 0.45, 1800.0)
        top_temp = 55.0
        bottom_temp = 98.0
    elif "crystallization" in separation_type or "filtration" in separation_type:
        service = "Crystallizer / filtration / dryer equivalent train"
        light_key = "Mother liquor"
        heavy_key = "Crystal product"
        alpha = 1.02
        stages = 4
        reflux = 0.10
        diameter = max(math.sqrt(product_mass / 12000.0), 1.2)
        height = 9.0
        reboiler = max(energy_balance.total_heating_kw * 0.30, 900.0)
        condenser = max(energy_balance.total_cooling_kw * 0.30, 900.0)
        top_temp = 45.0
        bottom_temp = 110.0
    elif "extraction" in separation_type:
        service = "Extraction and solvent recovery train"
        light_key = "Solvent-rich phase"
        heavy_key = "Product-rich phase"
        alpha = 1.15
        stages = 8
        reflux = 0.35
        diameter = max(math.sqrt(product_mass / 10000.0), 1.4)
        height = 14.0
        reboiler = max(energy_balance.total_heating_kw * 0.35, 1000.0)
        condenser = max(energy_balance.total_cooling_kw * 0.40, 950.0)
        top_temp = 62.0
        bottom_temp = 132.0
    else:
        service = "Distillation and purification train"
        light_key = "Water" if route.route_id == "eo_hydration" else "Light phase"
        heavy_key = "Ethylene glycol" if route.route_id == "eo_hydration" else "Heavy/product phase"
        alpha = 2.10
        stages = max(10, int(round(product_mass / 5000.0)) + 8)
        reflux = 1.45
        diameter = max(math.sqrt(product_mass / 8000.0), 1.8)
        height = stages * 0.75 + 4.0
        reboiler = max(energy_balance.total_heating_kw * 0.55, 1200.0)
        condenser = max(energy_balance.total_cooling_kw * 0.50, 1100.0)
        top_temp = 92.0
        bottom_temp = 198.0
    feed_stage = max(int(round(stages * 0.55)), 2)
    tray_spacing = 0.45
    flooding_fraction = min(max((product_mass / max(diameter ** 2 * 12000.0, 1.0)), 0.45), 0.82)
    downcomer_fraction = 0.14 if "distillation" in service.lower() else 0.10
    traces = [
        CalcTrace(trace_id="process_unit_service", title="Process-unit family", formula="service = selected separation family", result=service, units=""),
        CalcTrace(trace_id="process_unit_size", title="Equivalent diameter", formula="D = f(product throughput)", substitutions={"product_mass": f"{product_mass:.3f}"}, result=f"{diameter:.3f}", units="m"),
        CalcTrace(trace_id="process_unit_flooding", title="Flooding fraction", formula="fraction = superficial load / capacity proxy", substitutions={"product_mass": f"{product_mass:.3f}", "diameter": f"{diameter:.3f}"}, result=f"{flooding_fraction:.3f}", units="-"),
    ]
    return ColumnDesign(
        column_id="PU-201",
        service=service,
        light_key=light_key,
        heavy_key=heavy_key,
        relative_volatility=round(alpha, 3),
        min_stages=round(max(stages * 0.6, 2.0), 3),
        design_stages=stages,
        reflux_ratio=round(reflux, 3),
        column_diameter_m=round(diameter, 3),
        column_height_m=round(height, 3),
        condenser_duty_kw=round(condenser, 3),
        reboiler_duty_kw=round(reboiler, 3),
        feed_stage=feed_stage,
        tray_spacing_m=tray_spacing,
        flooding_fraction=round(flooding_fraction, 3),
        downcomer_area_fraction=round(downcomer_fraction, 3),
        top_temperature_c=round(top_temp, 1),
        bottom_temperature_c=round(bottom_temp, 1),
        calc_traces=traces,
        value_records=[
            make_value_record("process_unit_stages", "Process-unit design stages", stages, "stages", citations=route.citations, assumptions=route.assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("process_unit_reboiler_duty", "Process-unit heating duty", reboiler, "kW", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=sorted(set(route.citations + energy_balance.citations + (separation_choice.citations if separation_choice else []))),
        assumptions=route.assumptions + energy_balance.assumptions + (separation_choice.assumptions if separation_choice else []),
    )


def build_heat_exchanger_design_generic(
    route: RouteOption,
    energy_balance: EnergyBalance,
    exchanger_choice: DecisionRecord | None = None,
) -> HeatExchangerDesign:
    exchanger_type = exchanger_choice.selected_candidate_id if exchanger_choice and exchanger_choice.selected_candidate_id else "shell_and_tube"
    duty = max((item.heating_kw or item.cooling_kw) for item in energy_balance.duties if item.unit_id.startswith("E-") or item.unit_id.startswith("D-") or item.unit_id.startswith("DRY"))
    if "plate" in exchanger_type:
        u_value = 900.0
        lmtd = 18.0
    elif "air" in exchanger_type:
        u_value = 150.0
        lmtd = 28.0
    elif "kettle" in exchanger_type or "thermosyphon" in exchanger_type:
        u_value = 650.0
        lmtd = 22.0
    else:
        u_value = 520.0
        lmtd = 30.0
    area = max(duty * 1000.0 / max(u_value * lmtd, 1.0), 1.0)
    tube_length = 4.8 if "shell" in exchanger_type or "kettle" in exchanger_type else 2.2
    tube_area = math.pi * 0.019 * tube_length
    tube_count = max(int(math.ceil(area / max(tube_area, 1e-6))), 12)
    shell_diameter = max(math.sqrt(area / 12.0), 0.5)
    return HeatExchangerDesign(
        exchanger_id="E-101",
        service=exchanger_type.replace("_", " ").title(),
        heat_load_kw=round(duty, 3),
        lmtd_k=round(lmtd, 3),
        overall_u_w_m2_k=round(u_value, 3),
        area_m2=round(area, 3),
        exchanger_type=exchanger_type.replace("_", " ").title(),
        shell_diameter_m=round(shell_diameter, 3),
        tube_count=tube_count,
        tube_length_m=round(tube_length, 3),
        shell_passes=1,
        tube_passes=2 if "plate" not in exchanger_type else 1,
        calc_traces=[CalcTrace(trace_id="exchanger_area", title="Exchanger area", formula="A = Q/(U*dTlm)", substitutions={"Q": f"{duty * 1000.0:.1f}", "U": f"{u_value:.1f}", "dTlm": f"{lmtd:.1f}"}, result=f"{area:.3f}", units="m2")],
        value_records=[
            make_value_record("exchanger_area", "Exchanger area", area, "m2", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=sorted(set(energy_balance.citations + (exchanger_choice.citations if exchanger_choice else []))),
        assumptions=energy_balance.assumptions + (exchanger_choice.assumptions if exchanger_choice else []),
    )


def build_storage_design_generic(
    basis: ProjectBasis,
    product_density_kg_m3: float,
    citations: list[str],
    assumptions: list[str],
    storage_choice: DecisionRecord | None = None,
) -> StorageDesign:
    storage_type = storage_choice.selected_candidate_id if storage_choice and storage_choice.selected_candidate_id else "vertical_tank_farm"
    if "silo" in storage_type or "hopper" in storage_type:
        inventory_days = 5.0
        density = max(product_density_kg_m3, 700.0)
        moc = "Carbon steel"
    elif "pressure" in storage_type:
        inventory_days = 3.0
        density = max(product_density_kg_m3, 850.0)
        moc = "Carbon steel"
    else:
        inventory_days = 7.0 if basis.capacity_tpa >= 100000 else 4.0
        density = product_density_kg_m3
        moc = "SS304"
    working_volume = basis.capacity_tpa * 1000.0 / (basis.annual_operating_days * 24.0) * inventory_days * 24.0 / max(density, 1.0)
    total_volume = working_volume * 1.12
    diameter = max((4.0 * total_volume / (math.pi * 4.0)) ** (1.0 / 3.0), 2.0)
    height = max(total_volume / (math.pi * (diameter / 2.0) ** 2), 3.0)
    return StorageDesign(
        storage_id="TK-301",
        service=f"{basis.target_product} storage via {storage_type.replace('_', ' ')}",
        inventory_days=inventory_days,
        working_volume_m3=round(working_volume, 3),
        total_volume_m3=round(total_volume, 3),
        material_of_construction=moc,
        diameter_m=round(diameter, 3),
        straight_side_height_m=round(height, 3),
        calc_traces=[CalcTrace(trace_id="storage_volume", title="Storage volume", formula="V = throughput * days / density", substitutions={"days": f"{inventory_days:.1f}"}, result=f"{working_volume:.3f}", units="m3")],
        value_records=[
            make_value_record("storage_inventory_days", "Inventory days", inventory_days, "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("storage_total_volume", "Storage total volume", total_volume, "m3", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
        ],
        citations=sorted(set(citations + (storage_choice.citations if storage_choice else []))),
        assumptions=assumptions + (storage_choice.assumptions if storage_choice else []),
    )


def build_equipment_list_generic(
    route: RouteOption,
    reactor: ReactorDesign,
    column: ColumnDesign,
    exchanger: HeatExchangerDesign,
    storage: StorageDesign,
    energy_balance: EnergyBalance,
    moc_decision: DecisionRecord | None = None,
) -> list[EquipmentSpec]:
    moc = moc_decision.selected_candidate_id.replace("_", " ").title() if moc_decision and moc_decision.selected_candidate_id else storage.material_of_construction
    flash_volume = max(reactor.design_volume_m3 * 0.18, 3.0)
    process_unit_type = "Distillation column" if "distillation" in column.service.lower() else "Absorber" if "absorption" in column.service.lower() else "Crystallizer train" if "crystallizer" in column.service.lower() else "Extraction column"
    return [
        EquipmentSpec(
            equipment_id=reactor.reactor_id,
            equipment_type="Reactor",
            service=reactor.reactor_type,
            design_basis=reactor.design_basis,
            volume_m3=reactor.design_volume_m3,
            design_temperature_c=reactor.design_temperature_c,
            design_pressure_bar=reactor.design_pressure_bar,
            material_of_construction=moc,
            duty_kw=reactor.heat_duty_kw,
            notes="Selector-driven reactor basis.",
            citations=reactor.citations,
            assumptions=reactor.assumptions,
        ),
        EquipmentSpec(
            equipment_id=column.column_id,
            equipment_type=process_unit_type,
            service=column.service,
            design_basis=f"{column.design_stages} stages equivalent",
            volume_m3=round(math.pi * (column.column_diameter_m / 2.0) ** 2 * max(column.column_height_m, 4.0), 3),
            design_temperature_c=140.0,
            design_pressure_bar=2.0,
            material_of_construction=moc,
            duty_kw=column.reboiler_duty_kw,
            notes="Selector-driven process-unit envelope.",
            citations=column.citations,
            assumptions=column.assumptions,
        ),
        EquipmentSpec(
            equipment_id="V-101",
            equipment_type="Flash drum",
            service="Intermediate disengagement",
            design_basis="Generic separator hold-up",
            volume_m3=round(flash_volume, 3),
            design_temperature_c=85.0,
            design_pressure_bar=3.0,
            material_of_construction=moc,
            notes="Generic separation hold-up vessel.",
            citations=reactor.citations,
            assumptions=reactor.assumptions,
        ),
        EquipmentSpec(
            equipment_id=exchanger.exchanger_id,
            equipment_type="Heat exchanger",
            service=exchanger.service,
            design_basis=f"LMTD {exchanger.lmtd_k:.1f} K",
            volume_m3=round(exchanger.area_m2 * 0.08, 3),
            design_temperature_c=180.0,
            design_pressure_bar=8.0,
            material_of_construction=moc,
            duty_kw=exchanger.heat_load_kw,
            notes="Selector-driven exchanger basis.",
            citations=exchanger.citations,
            assumptions=exchanger.assumptions,
        ),
        EquipmentSpec(
            equipment_id=storage.storage_id,
            equipment_type="Storage tank",
            service=storage.service,
            design_basis=f"{storage.inventory_days:.1f} days inventory",
            volume_m3=storage.total_volume_m3,
            design_temperature_c=45.0,
            design_pressure_bar=1.2,
            material_of_construction=storage.material_of_construction,
            notes="Selector-driven storage basis.",
            citations=storage.citations,
            assumptions=storage.assumptions,
        ),
    ]
