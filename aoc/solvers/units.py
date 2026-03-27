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
    UnitOperationPacket,
    UnitThermalPacket,
    UtilityArchitectureDecision,
)
from aoc.solvers.composition import (
    component_mass_fraction,
    composition_state_for_unit,
    estimate_bulk_density_kg_m3,
    estimate_bulk_viscosity_pa_s,
    light_heavy_keys,
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


def _unit_operation_packet(
    stream_table: StreamTable,
    *,
    unit_ids: tuple[str, ...] = (),
    unit_types: tuple[str, ...] = (),
) -> UnitOperationPacket | None:
    for packet in stream_table.unit_operation_packets:
        if unit_ids and packet.unit_id in unit_ids:
            return packet
        if unit_types and packet.unit_type in unit_types:
            return packet
    return None


def _thermal_packet(
    energy_balance: EnergyBalance,
    *,
    unit_ids: tuple[str, ...] = (),
    prefer: str = "any",
) -> UnitThermalPacket | None:
    matches = [
        packet
        for packet in energy_balance.unit_thermal_packets
        if not unit_ids or packet.unit_id in unit_ids
    ]
    if prefer == "heating":
        matches = [packet for packet in matches if packet.heating_kw > 0.0] or matches
    elif prefer == "cooling":
        matches = [packet for packet in matches if packet.cooling_kw > 0.0] or matches
    return max(matches, key=lambda packet: max(packet.heating_kw, packet.cooling_kw), default=None)


def _train_steps_for_units(
    utility_architecture: UtilityArchitectureDecision | None,
    *,
    source_unit_ids: tuple[str, ...] = (),
    sink_unit_ids: tuple[str, ...] = (),
) -> list:
    if utility_architecture is None:
        return []
    return [
        step
        for step in utility_architecture.architecture.selected_train_steps
        if (source_unit_ids and step.source_unit_id in source_unit_ids)
        or (sink_unit_ids and step.sink_unit_id in sink_unit_ids)
    ]


def _heat_stream_lookup(
    utility_architecture: UtilityArchitectureDecision | None,
) -> dict[str, object]:
    if utility_architecture is None or utility_architecture.architecture.heat_stream_set is None:
        return {}
    heat_streams = (
        utility_architecture.architecture.heat_stream_set.hot_streams
        + utility_architecture.architecture.heat_stream_set.cold_streams
    )
    return {stream.stream_id: stream for stream in heat_streams}


def _step_lmtd_k(step, heat_stream_lookup: dict[str, object]) -> float:
    hot_stream = heat_stream_lookup.get(step.hot_stream_id)
    cold_stream = heat_stream_lookup.get(step.cold_stream_id)
    if hot_stream is None or cold_stream is None:
        return 18.0
    dt1 = max(hot_stream.supply_temp_c - cold_stream.target_temp_c, 8.0)
    dt2 = max(hot_stream.target_temp_c - cold_stream.supply_temp_c, 8.0)
    if abs(dt1 - dt2) <= 1e-6:
        return dt1
    ratio = max(dt1 / max(dt2, 1e-6), 1.0001)
    return max((dt1 - dt2) / math.log(ratio), 8.0)


def _weighted_lmtd_k(steps: list, heat_stream_lookup: dict[str, object]) -> float:
    weighted_duty = sum(step.recovered_duty_kw for step in steps)
    if weighted_duty <= 0.0:
        return 0.0
    return sum(step.recovered_duty_kw * _step_lmtd_k(step, heat_stream_lookup) for step in steps) / weighted_duty


def _step_media_summary(steps: list) -> str:
    media = []
    for step in steps:
        if step.medium not in media:
            media.append(step.medium)
    return " / ".join(media)


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
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> ReactorDesign:
    reactor_type = reactor_choice.selected_candidate_id if reactor_choice and reactor_choice.selected_candidate_id else "jacketed_cstr"
    reactor_packet = _unit_operation_packet(stream_table, unit_ids=("reactor",), unit_types=("reactor",))
    reactor_state = composition_state_for_unit(stream_table.composition_states, unit_ids=("reactor",), unit_types=("reactor",))
    feed_mass = reactor_packet.inlet_mass_flow_kg_hr if reactor_packet is not None else _feed_mass(stream_table)
    density = estimate_bulk_density_kg_m3(
        reactor_state,
        1150.0 if "solid" in reactor_type else 1020.0 if "aqueous" in reactor_type or "hydrator" in reactor_type else 900.0,
    )
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
    reactor_thermal = _thermal_packet(energy_balance, unit_ids=("R-101", "CONV-101"), prefer="cooling")
    reactor_train_steps = _train_steps_for_units(
        utility_architecture,
        source_unit_ids=("R-101", "CONV-101", "reactor"),
        sink_unit_ids=("R-101", "CONV-101", "reactor"),
    )
    heat_stream_lookup = _heat_stream_lookup(utility_architecture)
    integrated_recovery = sum(step.recovered_duty_kw for step in reactor_train_steps)
    reactor_duty = max(
        reactor_thermal.cooling_kw if reactor_thermal and reactor_thermal.cooling_kw > 0.0 else 0.0,
        reactor_thermal.heating_kw if reactor_thermal and reactor_thermal.heating_kw > 0.0 else 0.0,
        _duty_for_prefix(energy_balance, ("R-", "CONV")),
    )
    uses_htm_loop = any(step.medium.lower() != "direct" for step in reactor_train_steps)
    u_value = 500.0 if uses_htm_loop else 850.0 if "plug_flow" in reactor_type or "hydrator" in reactor_type else 600.0
    if reactor_thermal is not None:
        lmtd = max(
            (
                reactor_thermal.hot_supply_temp_c - reactor_thermal.cold_target_temp_c
                if reactor_duty > 0 and reactor_thermal.cooling_kw > 0.0
                else reactor_thermal.cold_target_temp_c - reactor_thermal.cold_supply_temp_c
            ),
            18.0,
        )
    else:
        lmtd = 24.0 if reactor_duty > 0 else 18.0
    integrated_lmtd = _weighted_lmtd_k(reactor_train_steps, heat_stream_lookup)
    integrated_recovery_effective = min(integrated_recovery, reactor_duty)
    integrated_area = (
        max((integrated_recovery_effective * 1000.0) / max(u_value * max(integrated_lmtd, 1.0), 1.0), 0.0)
        if integrated_recovery_effective > 0.0
        else 0.0
    )
    area = max((reactor_duty * 1000.0) / max(u_value * lmtd, 1.0), 1.0)
    shell_diameter = max((4.0 * design_volume / (math.pi * 5.0)) ** (1.0 / 3.0), 1.1)
    shell_length = max(design_volume / (math.pi * (shell_diameter / 2.0) ** 2), 4.5)
    viscosity_pa_s = estimate_bulk_viscosity_pa_s(reactor_state, 0.0018 if "hydrator" in reactor_type else 0.0024)
    hydraulic_diameter_m = 0.032 if "plug_flow" in reactor_type or "hydrator" in reactor_type else 0.055
    velocity_m_s = max((volumetric_flow_m3_hr / 3600.0) / max(math.pi * (shell_diameter / 2.0) ** 2 * 0.55, 1e-6), 0.2)
    reynolds = max((density * velocity_m_s * hydraulic_diameter_m) / max(viscosity_pa_s, 1e-6), 1000.0)
    water_fraction = max(component_mass_fraction(reactor_state, "Water", side="inlet"), component_mass_fraction(reactor_state, "Water"))
    prandtl = 7.5 + water_fraction * 5.5 if "hydrator" in reactor_type else 6.5 + water_fraction * 4.0
    nusselt = 0.023 * (reynolds ** 0.8) * (prandtl ** 0.4)
    tube_length = max(shell_length * 0.88, 4.0)
    tube_area = math.pi * 0.025 * tube_length
    tube_count = max(int(math.ceil(area / max(tube_area, 1e-6))), 24)
    integrated_media = _step_media_summary(reactor_train_steps)
    if integrated_media:
        cooling_medium = integrated_media
    elif reactor_thermal and reactor_thermal.candidate_media:
        cooling_medium = " / ".join(reactor_thermal.candidate_media[:2])
    else:
        cooling_medium = "Dowtherm / cooling water" if reactor_duty > 0 else "Steam / hot oil"
    traces = [
        CalcTrace(trace_id="reactor_holdup", title="Reactor holdup", formula="V = Qv * tau * factor", substitutions={"Qv": f"{volumetric_flow_m3_hr:.3f}", "tau": f"{residence_time:.3f}"}, result=f"{liquid_holdup_m3:.3f}", units="m3"),
        CalcTrace(trace_id="reactor_design_volume", title="Reactor design volume", formula="Vd = V * design_factor", substitutions={"V": f"{liquid_holdup_m3:.3f}", "factor": f"{design_factor:.3f}"}, result=f"{design_volume:.3f}", units="m3"),
        CalcTrace(trace_id="reactor_reynolds", title="Reactor-side Reynolds number", formula="Re = rho * v * Dh / mu", substitutions={"rho": f"{density:.1f}", "v": f"{velocity_m_s:.3f}", "Dh": f"{hydraulic_diameter_m:.3f}", "mu": f"{viscosity_pa_s:.5f}"}, result=f"{reynolds:.1f}", units="-"),
        CalcTrace(trace_id="reactor_nusselt", title="Reactor-side Nusselt number", formula="Nu = 0.023 Re^0.8 Pr^0.4", substitutions={"Re": f"{reynolds:.1f}", "Pr": f"{prandtl:.2f}"}, result=f"{nusselt:.2f}", units="-"),
        CalcTrace(
            trace_id="reactor_packet_basis",
            title="Solved reactor packet basis",
            formula="reactor packet -> inlet mass and thermal duty",
            substitutions={
                "packet_inlet_mass_kg_hr": f"{reactor_packet.inlet_mass_flow_kg_hr:.3f}" if reactor_packet else "fallback",
                "thermal_packet": reactor_thermal.packet_id if reactor_thermal else "fallback",
                "composition_state": reactor_state.state_id if reactor_state else "fallback",
            },
            result=f"{reactor_duty:.3f}",
            units="kW",
            notes="Reactor sizing now reads the solved reactor unit packet, composition state, and thermal packet before falling back to route-level heuristics.",
        ),
        CalcTrace(
            trace_id="reactor_utility_integration_basis",
            title="Reactor utility-train coupling",
            formula="Integrated reactor duty = sum(selected train steps tied to reactor source/sink)",
            substitutions={
                "selected_steps": ", ".join(step.step_id for step in reactor_train_steps) or "none",
                "topology": utility_architecture.architecture.topology_summary if utility_architecture else "none",
            },
            result=f"{integrated_recovery:.3f}",
            units="kW",
            notes="This captures recovered reactor duty exported to or imported from the selected utility train.",
        ),
        CalcTrace(
            trace_id="reactor_integrated_heat_transfer",
            title="Reactor integrated heat-transfer basis",
            formula="A_int = Q_int / (U * LMTD_int)",
            substitutions={
                "Q_int": f"{integrated_recovery_effective * 1000.0:.1f}",
                "U": f"{u_value:.1f}",
                "LMTD_int": f"{integrated_lmtd:.2f}",
            },
            result=f"{integrated_area:.3f}",
            units="m2",
            notes="Integrated heat-transfer area is derived from the selected train-step thermal driving force, not only aggregate recovered duty.",
        ),
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
        cooling_medium=cooling_medium,
        utility_topology=utility_architecture.architecture.topology_summary if utility_architecture else "",
        integrated_thermal_duty_kw=round(integrated_recovery, 3),
        residual_utility_duty_kw=round(max(reactor_duty - integrated_recovery, 0.0), 3),
        integrated_lmtd_k=round(integrated_lmtd, 3),
        integrated_exchange_area_m2=round(integrated_area, 3),
        coupled_service_basis="; ".join(f"{step.service} via {step.medium}" for step in reactor_train_steps) or "standalone utility service",
        selected_train_step_ids=[step.step_id for step in reactor_train_steps],
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
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> ColumnDesign:
    separation_type = separation_choice.selected_candidate_id if separation_choice and separation_choice.selected_candidate_id else "distillation_train"
    if "absorption" in separation_type:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("regeneration",), unit_types=("stripping",))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("STR-201",), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("ABS-201", "STR-201"), prefer="cooling")
    elif "crystallization" in separation_type or "filtration" in separation_type:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("filtration", "drying"), unit_types=("filtration", "drying"))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("DRY-301",), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("CRYS-201", "FILT-201"), prefer="cooling")
    elif "extraction" in separation_type:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("purification",), unit_types=("extraction",))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("SR-301", "EXT-201"), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("DEC-201", "EXT-201"), prefer="cooling")
    else:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("purification",), unit_types=("distillation", "evaporation"))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("D-101", "EV-101"), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("D-101", "V-101", "E-201"), prefer="cooling")
    process_state = composition_state_for_unit(
        stream_table.composition_states,
        unit_ids=("purification", "concentration", "regeneration", "filtration", "drying"),
        unit_types=("distillation", "evaporation", "stripping", "filtration", "drying", "extraction"),
    )
    product_mass = (
        max(process_packet.outlet_mass_flow_kg_hr * 0.72, _product_mass(stream_table))
        if process_packet is not None and process_packet.outlet_mass_flow_kg_hr > 0.0
        else _product_mass(stream_table)
    )
    if "absorption" in separation_type:
        service = "Absorption tower train"
        light_key = "Offgas"
        heavy_key = "Rich absorbent"
        alpha = 1.08
        stages = 10
        reflux = 0.20
        diameter = max(math.sqrt(product_mass / 9000.0), 1.5)
        height = 18.0
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.18, 1200.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.45, 1800.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 55.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 98.0
    elif "crystallization" in separation_type or "filtration" in separation_type:
        service = "Crystallizer / filtration / dryer equivalent train"
        light_key = "Mother liquor"
        heavy_key = "Crystal product"
        alpha = 1.02
        stages = 4
        reflux = 0.10
        diameter = max(math.sqrt(product_mass / 12000.0), 1.2)
        height = 9.0
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.30, 900.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.30, 900.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 45.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 110.0
    elif "extraction" in separation_type:
        service = "Extraction and solvent recovery train"
        light_key = "Solvent-rich phase"
        heavy_key = "Product-rich phase"
        alpha = 1.15
        stages = 8
        reflux = 0.35
        diameter = max(math.sqrt(product_mass / 10000.0), 1.4)
        height = 14.0
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.35, 1000.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.40, 950.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 62.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 132.0
    else:
        service = "Distillation and purification train"
        light_key, heavy_key = light_heavy_keys(process_state)
        if route.route_id == "eo_hydration" and light_key == "Light key":
            light_key, heavy_key = "Water", "Ethylene glycol"
        complexity = len(process_state.outlet_component_mole_fraction) if process_state is not None else 2
        alpha = max(1.15, 2.40 - 0.18 * max(complexity - 2, 0))
        stages = max(10, int(round(product_mass / 5000.0)) + 8)
        reflux = 1.45
        diameter = max(math.sqrt(product_mass / 8000.0), 1.8)
        height = stages * 0.75 + 4.0
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.55, 1200.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.50, 1100.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 92.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 198.0
    process_unit_ids = ("purification", "concentration", "regeneration", "drying", "filtration")
    heating_train_steps = _train_steps_for_units(utility_architecture, sink_unit_ids=process_unit_ids)
    condenser_train_steps = _train_steps_for_units(utility_architecture, source_unit_ids=process_unit_ids)
    heat_stream_lookup = _heat_stream_lookup(utility_architecture)
    integrated_reboiler = sum(step.recovered_duty_kw for step in heating_train_steps)
    condenser_recovery = sum(step.recovered_duty_kw for step in condenser_train_steps)
    integrated_reboiler_effective = min(integrated_reboiler, reboiler)
    condenser_recovery_effective = min(condenser_recovery, condenser)
    reboiler_lmtd = _weighted_lmtd_k(heating_train_steps, heat_stream_lookup)
    condenser_lmtd = _weighted_lmtd_k(condenser_train_steps, heat_stream_lookup)
    reboiler_u = 620.0 if any(step.medium.lower() != "direct" for step in heating_train_steps) else 780.0
    condenser_u = 520.0 if any(step.medium.lower() != "direct" for step in condenser_train_steps) else 700.0
    reboiler_area = (
        max((integrated_reboiler_effective * 1000.0) / max(reboiler_u * max(reboiler_lmtd, 1.0), 1.0), 0.0)
        if integrated_reboiler_effective > 0.0
        else 0.0
    )
    condenser_area = (
        max((condenser_recovery_effective * 1000.0) / max(condenser_u * max(condenser_lmtd, 1.0), 1.0), 0.0)
        if condenser_recovery_effective > 0.0
        else 0.0
    )
    feed_stage = max(int(round(stages * 0.55)), 2)
    tray_spacing = 0.45
    flooding_fraction = min(max((product_mass / max(diameter ** 2 * 12000.0, 1.0)), 0.45), 0.82)
    downcomer_fraction = 0.14 if "distillation" in service.lower() else 0.10
    traces = [
        CalcTrace(trace_id="process_unit_service", title="Process-unit family", formula="service = selected separation family", result=service, units=""),
        CalcTrace(trace_id="process_unit_size", title="Equivalent diameter", formula="D = f(product throughput)", substitutions={"product_mass": f"{product_mass:.3f}"}, result=f"{diameter:.3f}", units="m"),
        CalcTrace(trace_id="process_unit_flooding", title="Flooding fraction", formula="fraction = superficial load / capacity proxy", substitutions={"product_mass": f"{product_mass:.3f}", "diameter": f"{diameter:.3f}"}, result=f"{flooding_fraction:.3f}", units="-"),
        CalcTrace(
            trace_id="column_packet_basis",
            title="Solved process-unit packet basis",
            formula="packet basis -> outlet throughput and matched thermal packets",
            substitutions={
                "process_packet": process_packet.packet_id if process_packet else "fallback",
                "heating_packet": heating_packet.packet_id if heating_packet else "fallback",
                "cooling_packet": cooling_packet.packet_id if cooling_packet else "fallback",
                "composition_state": process_state.state_id if process_state else "fallback",
            },
            result=f"{reboiler:.3f}",
            units="kW",
            notes="Process-unit sizing now prefers solved separation packet, composition state, and thermal packet before route-level utility heuristics.",
        ),
        CalcTrace(
            trace_id="column_utility_integration_basis",
            title="Process-unit utility-train coupling",
            formula="Integrated reboiler duty = sum(selected train steps tied to process-unit cold sinks",
            substitutions={
                "heating_steps": ", ".join(step.step_id for step in heating_train_steps) or "none",
                "condenser_steps": ", ".join(step.step_id for step in condenser_train_steps) or "none",
                "topology": utility_architecture.architecture.topology_summary if utility_architecture else "none",
            },
            result=f"{integrated_reboiler:.3f}",
            units="kW",
            notes="This captures recovered duty delivered into the reboiler/process unit and heat recovered from condenser-side streams.",
        ),
        CalcTrace(
            trace_id="column_reboiler_integrated_heat_transfer",
            title="Integrated reboiler heat-transfer basis",
            formula="A_reb,int = Q_reb,int / (U_reb * LMTD_reb,int)",
            substitutions={
                "Q_reb,int": f"{integrated_reboiler_effective * 1000.0:.1f}",
                "U_reb": f"{reboiler_u:.1f}",
                "LMTD_reb,int": f"{reboiler_lmtd:.2f}",
            },
            result=f"{reboiler_area:.3f}",
            units="m2",
            notes="Integrated reboiler area is derived from selected train steps that feed the process-unit heating sink.",
        ),
        CalcTrace(
            trace_id="column_condenser_recovery_heat_transfer",
            title="Condenser-side recovery basis",
            formula="A_cond,rec = Q_cond,rec / (U_cond * LMTD_cond,rec)",
            substitutions={
                "Q_cond,rec": f"{condenser_recovery_effective * 1000.0:.1f}",
                "U_cond": f"{condenser_u:.1f}",
                "LMTD_cond,rec": f"{condenser_lmtd:.2f}",
            },
            result=f"{condenser_area:.3f}",
            units="m2",
            notes="Recovered condenser duty is tied to selected train steps sourced from the process-unit hot side.",
        ),
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
        utility_topology=utility_architecture.architecture.topology_summary if utility_architecture else "",
        integrated_reboiler_duty_kw=round(integrated_reboiler, 3),
        residual_reboiler_utility_kw=round(max(reboiler - integrated_reboiler, 0.0), 3),
        integrated_reboiler_lmtd_k=round(reboiler_lmtd, 3),
        integrated_reboiler_area_m2=round(reboiler_area, 3),
        reboiler_medium=_step_media_summary(heating_train_steps),
        condenser_recovery_duty_kw=round(condenser_recovery, 3),
        condenser_recovery_lmtd_k=round(condenser_lmtd, 3),
        condenser_recovery_area_m2=round(condenser_area, 3),
        condenser_recovery_medium=_step_media_summary(condenser_train_steps),
        selected_train_step_ids=[step.step_id for step in heating_train_steps + condenser_train_steps],
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
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> HeatExchangerDesign:
    selected_train_steps = utility_architecture.architecture.selected_train_steps if utility_architecture is not None else []
    exchanger_type = exchanger_choice.selected_candidate_id if exchanger_choice and exchanger_choice.selected_candidate_id else "shell_and_tube"
    prioritized_steps = [
        step
        for step in selected_train_steps
        if any(token in step.service.lower() for token in ("reboiler", "condenser"))
    ]
    selected_step = max(prioritized_steps or selected_train_steps, key=lambda step: step.recovered_duty_kw, default=None)
    selected_package_items = selected_step.package_items if selected_step is not None else []
    exchanger_package = next((item for item in selected_package_items if item.package_role == "exchanger"), None)
    preferred_unit_ids = tuple(
        unit_id
        for step in selected_train_steps
        for unit_id in (step.source_unit_id, step.sink_unit_id)
    )
    packet = _thermal_packet(
        energy_balance,
        unit_ids=preferred_unit_ids or ("E-101", "E-201", "D-101", "EV-101", "DRY-301", "STR-201"),
        prefer="heating",
    ) or _thermal_packet(
        energy_balance,
        unit_ids=preferred_unit_ids or ("E-101", "E-201", "D-101", "EV-101", "DRY-301", "STR-201"),
        prefer="cooling",
    )
    duty = max(
        exchanger_package.duty_kw if exchanger_package is not None else selected_step.recovered_duty_kw if selected_step is not None else 0.0,
        packet.heating_kw if packet and packet.heating_kw > 0.0 else 0.0,
        packet.cooling_kw if packet and packet.cooling_kw > 0.0 else 0.0,
        max((item.heating_kw or item.cooling_kw) for item in energy_balance.duties if item.unit_id.startswith("E-") or item.unit_id.startswith("D-") or item.unit_id.startswith("DRY")),
    )
    package_family = exchanger_package.package_family if exchanger_package is not None else ""
    if package_family == "reboiler":
        exchanger_type = "kettle_reboiler" if selected_step is not None and selected_step.medium.lower() != "direct" else "thermosyphon_reboiler"
    elif package_family == "condenser":
        exchanger_type = "surface_condenser" if selected_step is not None and selected_step.medium.lower() == "direct" else "htm_condensing_exchanger"
    elif selected_step is not None and selected_step.medium.lower() != "direct":
        exchanger_type = "kettle_reboiler" if "reboiler" in selected_step.service.lower() else exchanger_type
    elif selected_step is not None and "feed" in selected_step.service.lower():
        exchanger_type = "plate" if exchanger_choice is None else exchanger_type
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
    if exchanger_package is not None and exchanger_package.heat_transfer_area_m2 > 0.0:
        u_value = max((exchanger_package.duty_kw * 1000.0) / max(exchanger_package.heat_transfer_area_m2 * max(exchanger_package.lmtd_k, 1.0), 1.0), 1.0)
        lmtd = exchanger_package.lmtd_k
    if packet is not None:
        if exchanger_package is None and duty == packet.heating_kw:
            lmtd = max(packet.hot_supply_temp_c - packet.cold_target_temp_c, 12.0)
        elif exchanger_package is None:
            lmtd = max(packet.hot_supply_temp_c - packet.hot_target_temp_c, 12.0)
    area = exchanger_package.heat_transfer_area_m2 if exchanger_package is not None and exchanger_package.heat_transfer_area_m2 > 0.0 else max(duty * 1000.0 / max(u_value * lmtd, 1.0), 1.0)
    tube_length = 4.8 if "shell" in exchanger_type or "kettle" in exchanger_type else 2.2
    tube_area = math.pi * 0.019 * tube_length
    tube_count = max(int(math.ceil(area / max(tube_area, 1e-6))), 12)
    shell_diameter = max(math.sqrt(area / 12.0), 0.5)
    circulation_flow = exchanger_package.flow_m3_hr if exchanger_package is not None else 0.0
    phase_change_load = exchanger_package.phase_change_load_kg_hr if exchanger_package is not None else 0.0
    package_holdup = exchanger_package.volume_m3 if exchanger_package is not None else max(area * 0.05, 0.5)
    return HeatExchangerDesign(
        exchanger_id="E-101",
        service=selected_step.service if selected_step is not None else exchanger_type.replace("_", " ").title(),
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
        package_family=package_family or "generic",
        circulation_flow_m3_hr=round(circulation_flow, 3),
        phase_change_load_kg_hr=round(phase_change_load, 3),
        package_holdup_m3=round(package_holdup, 3),
        utility_topology=utility_architecture.architecture.topology_summary if utility_architecture is not None else "",
        selected_train_step_id=selected_step.step_id if selected_step is not None else None,
        selected_package_item_ids=[item.package_item_id for item in selected_package_items],
        calc_traces=[
            CalcTrace(trace_id="exchanger_area", title="Exchanger area", formula="A = Q/(U*dTlm)", substitutions={"Q": f"{duty * 1000.0:.1f}", "U": f"{u_value:.1f}", "dTlm": f"{lmtd:.1f}"}, result=f"{area:.3f}", units="m2"),
            CalcTrace(
                trace_id="exchanger_packet_basis",
                title="Solved exchanger packet basis",
                formula="packet basis -> selected thermal packet",
                substitutions={
                    "thermal_packet": packet.packet_id if packet else "fallback",
                    "selected_train_step": selected_step.step_id if selected_step else "fallback",
                },
                result=f"{duty:.3f}",
                units="kW",
                notes="Exchanger sizing now prefers the selected utility-train step and solved thermal packet before aggregate-duty fallback.",
            ),
            CalcTrace(
                trace_id="exchanger_package_basis",
                title="Utility package exchanger basis",
                formula="Selected exchanger package -> family, area, LMTD, circulation, phase load",
                substitutions={
                    "package_family": package_family or "generic",
                    "exchanger_package": exchanger_package.package_item_id if exchanger_package is not None else "fallback",
                    "circulation_flow_m3_hr": f"{circulation_flow:.3f}",
                    "phase_change_load_kg_hr": f"{phase_change_load:.3f}",
                },
                result=f"{package_holdup:.3f}",
                units="m3",
                notes="Reboiler/condenser package sizing now reads the selected utility package item before applying generic exchanger fallback.",
            ),
        ],
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
    utility_architecture: UtilityArchitectureDecision | None = None,
) -> list[EquipmentSpec]:
    moc = moc_decision.selected_candidate_id.replace("_", " ").title() if moc_decision and moc_decision.selected_candidate_id else storage.material_of_construction
    flash_volume = max(reactor.design_volume_m3 * 0.18, 3.0)
    process_unit_type = "Distillation column" if "distillation" in column.service.lower() else "Absorber" if "absorption" in column.service.lower() else "Crystallizer train" if "crystallizer" in column.service.lower() else "Extraction column"
    equipment = [
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
    if utility_architecture is not None:
        for package_item in utility_architecture.architecture.selected_package_items:
            package_assumptions = sorted(set(package_item.assumptions + [f"Utility train package role: {package_item.package_role}."]))
            equipment.append(
                EquipmentSpec(
                    equipment_id=package_item.equipment_id,
                    equipment_type=package_item.equipment_type,
                    service=package_item.service,
                    design_basis=f"Utility train package item for {package_item.parent_step_id}",
                    volume_m3=package_item.volume_m3,
                    design_temperature_c=package_item.design_temperature_c,
                    design_pressure_bar=package_item.design_pressure_bar,
                    material_of_construction=package_item.material_of_construction or moc,
                    duty_kw=package_item.duty_kw or package_item.power_kw,
                    notes=package_item.notes,
                    citations=package_item.citations,
                    assumptions=package_assumptions,
                )
            )
    return equipment
