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
    SeparationPacket,
    StorageDesign,
    StreamTable,
    UnitOperationPacket,
    UnitThermalPacket,
    UtilityArchitectureDecision,
)
from aoc.properties.models import MixturePropertyArtifact, PropertyPackageArtifact, SeparationThermoArtifact
from aoc.properties.sources import normalize_chemical_name
from aoc.solvers.composition import (
    component_mass_fraction,
    composition_state_for_unit,
    estimate_bulk_density_kg_m3,
    estimate_bulk_viscosity_pa_s,
    light_heavy_keys,
    mixture_package_for_state,
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


def _separation_packets(
    stream_table: StreamTable,
    *,
    unit_ids: tuple[str, ...] = (),
    families: tuple[str, ...] = (),
) -> list[SeparationPacket]:
    matches: list[SeparationPacket] = []
    for packet in stream_table.separation_packets:
        if unit_ids and packet.unit_id in unit_ids:
            matches.append(packet)
            continue
        if families and packet.separation_family in families:
            matches.append(packet)
    return matches


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


def _average_molecular_weight_g_mol(state, *, side: str = "outlet", default: float = 28.0) -> float:
    if state is None:
        return default
    if side == "inlet":
        total_mass = sum(state.inlet_component_mass_kg_hr.values())
        total_molar = sum(state.inlet_component_molar_kmol_hr.values())
    else:
        total_mass = sum(state.outlet_component_mass_kg_hr.values())
        total_molar = sum(state.outlet_component_molar_kmol_hr.values())
    if total_molar <= 1e-9:
        return default
    return max(total_mass / total_molar, 2.0)


def _latent_load_kg_hr(duty_kw: float, latent_kj_kg: float) -> float:
    if duty_kw <= 0.0 or latent_kj_kg <= 1e-6:
        return 0.0
    return duty_kw * 3600.0 / latent_kj_kg


def _select_package_item(steps: list, *, role: str = "exchanger", family: str | None = None):
    candidates = []
    for step in steps:
        for item in step.package_items:
            if item.package_role != role:
                continue
            if family is not None and item.package_family != family:
                continue
            candidates.append(item)
    return max(candidates, key=lambda item: max(item.duty_kw, item.heat_transfer_area_m2, item.flow_m3_hr, item.volume_m3), default=None)


def _stream_component_mass_kg_hr(
    stream_table: StreamTable,
    stream_ids: list[str],
    component_name: str,
) -> float:
    selected_ids = set(stream_ids)
    if not selected_ids:
        return 0.0
    target = normalize_chemical_name(component_name)
    return sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_id in selected_ids
        for component in stream.components
        if normalize_chemical_name(component.name) == target
    )


def _stream_component_molar_kmol_hr(
    stream_table: StreamTable,
    stream_ids: list[str],
    component_name: str,
) -> float:
    selected_ids = set(stream_ids)
    if not selected_ids:
        return 0.0
    target = normalize_chemical_name(component_name)
    return sum(
        component.molar_flow_kmol_hr
        for stream in stream_table.streams
        if stream.stream_id in selected_ids
        for component in stream.components
        if normalize_chemical_name(component.name) == target
    )


def _stream_total_mass_kg_hr(stream_table: StreamTable, stream_ids: list[str]) -> float:
    selected_ids = set(stream_ids)
    return sum(
        component.mass_flow_kg_hr
        for stream in stream_table.streams
        if stream.stream_id in selected_ids
        for component in stream.components
    )


def _average_stream_temperature_c(stream_table: StreamTable, stream_ids: list[str], fallback: float) -> float:
    selected = [stream.temperature_c for stream in stream_table.streams if stream.stream_id in set(stream_ids)]
    return sum(selected) / len(selected) if selected else fallback


def _preferred_equilibrium_component(packet: SeparationPacket, *, mode: str) -> str | None:
    component_names = (
        set(packet.component_split_to_product)
        | set(packet.component_split_to_waste)
        | set(packet.component_split_to_recycle)
    )
    if not component_names:
        return None
    excluded = {"water"} if mode == "sle" else {"water", "sulfuric_acid", "spent_acid"}
    ranked: list[tuple[float, float, str]] = []
    for component_name in component_names:
        normalized = normalize_chemical_name(component_name)
        if normalized in excluded:
            continue
        product_split = packet.component_split_to_product.get(component_name, 0.0)
        waste_split = packet.component_split_to_waste.get(component_name, 0.0)
        recycle_split = packet.component_split_to_recycle.get(component_name, 0.0)
        if mode == "gle":
            score = product_split + recycle_split - waste_split
        else:
            score = product_split - recycle_split - waste_split
        ranked.append((score, product_split + recycle_split + waste_split, component_name))
    if ranked:
        return max(ranked, key=lambda item: (item[0], item[1], item[2].lower()))[2]
    return max(sorted(component_names), key=lambda name: packet.component_split_to_product.get(name, 0.0), default=None)


def _lookup_henry_constant(
    property_packages: PropertyPackageArtifact | None,
    gas_name: str,
    solvent_name: str,
):
    if property_packages is None:
        return None
    gas_id = normalize_chemical_name(gas_name)
    solvent_id = normalize_chemical_name(solvent_name)
    return next(
        (
            item
            for item in property_packages.henry_law_constants
            if item.gas_component_id == gas_id and item.solvent_component_id == solvent_id and item.resolution_status == "resolved"
        ),
        None,
    )


def _lookup_solubility_curve(
    property_packages: PropertyPackageArtifact | None,
    solute_name: str,
    solvent_name: str,
):
    if property_packages is None:
        return None
    solute_id = normalize_chemical_name(solute_name)
    solvent_id = normalize_chemical_name(solvent_name)
    return next(
        (
            item
            for item in property_packages.solubility_curves
            if item.solute_component_id == solute_id and item.solvent_component_id == solvent_id and item.resolution_status == "resolved"
        ),
        None,
    )


def _evaluate_solubility_curve(curve, temperature_c: float) -> float | None:
    if curve is None:
        return None
    if curve.equation_name.lower() == "linear":
        a = float(curve.parameters.get("a", 0.0))
        b = float(curve.parameters.get("b", 0.0))
        return max(a + b * temperature_c, 0.0)
    return None


def _fenske_min_stages(alpha: float, xD_lk: float, xB_lk: float, xD_hk: float, xB_hk: float) -> float:
    alpha = max(alpha, 1.02)
    numerator = max((xD_lk / max(xB_lk, 1e-4)) * (xB_hk / max(xD_hk, 1e-4)), 1.0001)
    return max(math.log(numerator) / math.log(alpha), 2.0)


def _underwood_min_reflux_proxy(alpha: float, q: float, xD_lk: float) -> float:
    alpha = max(alpha, 1.02)
    q = min(max(q, 0.7), 1.6)
    return max(((alpha * max(xD_lk, 0.5)) / max(alpha - 1.0, 0.08) - 1.0) * (0.55 + 0.25 * q), 0.15)


def _tray_efficiency_proxy(viscosity_pa_s: float, alpha: float, service: str) -> float:
    viscosity_penalty = min(max(viscosity_pa_s / 0.0035, 0.0), 1.0)
    volatility_bonus = min(max((alpha - 1.0) / 1.5, 0.0), 1.0)
    base = 0.58 + 0.18 * volatility_bonus - 0.10 * viscosity_penalty
    if "absorption" in service.lower():
        base += 0.05
    elif "crystallizer" in service.lower() or "dryer" in service.lower():
        base -= 0.08
    return min(max(base, 0.42), 0.82)


def _gilliland_actual_stages_proxy(nmin: float, rmin: float, reflux_ratio: float) -> float:
    if reflux_ratio <= 0.0:
        return max(nmin * 1.6, nmin + 2.0)
    x = (reflux_ratio - rmin) / max(reflux_ratio + 1.0, 1.0)
    x = min(max(x, 0.02), 0.95)
    y = 0.78 * (1.0 - math.exp(-1.35 * x)) + 0.10
    y = min(max(y, 0.15), 0.92)
    return max((nmin + y) / max(1.0 - y, 0.08), nmin + 1.0)


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
    mixture_properties: MixturePropertyArtifact | None = None,
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
        mixture_properties=mixture_properties,
        unit_ids=("reactor",),
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
    viscosity_pa_s = estimate_bulk_viscosity_pa_s(
        reactor_state,
        0.0018 if "hydrator" in reactor_type else 0.0024,
        mixture_properties=mixture_properties,
        unit_ids=("reactor",),
    )
    reactor_mixture = mixture_package_for_state(reactor_state, mixture_properties, unit_ids=("reactor",))
    thermal_conductivity = reactor_mixture.thermal_conductivity_w_m_k if reactor_mixture and reactor_mixture.thermal_conductivity_w_m_k else 0.18
    heat_capacity = reactor_mixture.liquid_heat_capacity_kj_kg_k if reactor_mixture and reactor_mixture.liquid_heat_capacity_kj_kg_k else (4.0 if "hydrator" in reactor_type else 2.5)
    hydraulic_diameter_m = 0.032 if "plug_flow" in reactor_type or "hydrator" in reactor_type else 0.055
    velocity_m_s = max((volumetric_flow_m3_hr / 3600.0) / max(math.pi * (shell_diameter / 2.0) ** 2 * 0.55, 1e-6), 0.2)
    reynolds = max((density * velocity_m_s * hydraulic_diameter_m) / max(viscosity_pa_s, 1e-6), 1000.0)
    water_fraction = max(component_mass_fraction(reactor_state, "Water", side="inlet"), component_mass_fraction(reactor_state, "Water"))
    prandtl = max((heat_capacity * 1000.0 * viscosity_pa_s) / max(thermal_conductivity, 1e-6), 1.0)
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
            trace_id="reactor_property_basis",
            title="Reactor property-package basis",
            formula="Pr = Cp * mu / k using mixture-property package values when available",
            substitutions={
                "Cp": f"{heat_capacity:.3f}",
                "mu": f"{viscosity_pa_s:.6f}",
                "k": f"{thermal_conductivity:.4f}",
                "mixture_package": reactor_mixture.mixture_id if reactor_mixture else "fallback",
            },
            result=f"{prandtl:.2f}",
            units="-",
        ),
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
    mixture_properties: MixturePropertyArtifact | None = None,
    separation_choice: DecisionRecord | None = None,
    utility_architecture: UtilityArchitectureDecision | None = None,
    separation_thermo: SeparationThermoArtifact | None = None,
    property_packages: PropertyPackageArtifact | None = None,
) -> ColumnDesign:
    separation_type = separation_choice.selected_candidate_id if separation_choice and separation_choice.selected_candidate_id else "distillation_train"
    equilibrium_packets: list[SeparationPacket] = []
    if "absorption" in separation_type:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("regeneration",), unit_types=("stripping",))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("STR-201",), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("ABS-201", "STR-201"), prefer="cooling")
        equilibrium_packets = _separation_packets(
            stream_table,
            unit_ids=("primary_separation", "regeneration"),
            families=("absorption", "stripping"),
        )
    elif "crystallization" in separation_type or "filtration" in separation_type:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("filtration", "drying"), unit_types=("filtration", "drying"))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("DRY-301",), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("CRYS-201", "FILT-201"), prefer="cooling")
        equilibrium_packets = _separation_packets(
            stream_table,
            unit_ids=("concentration", "filtration", "drying"),
            families=("crystallization", "filtration", "drying"),
        )
    elif "extraction" in separation_type:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("purification",), unit_types=("extraction",))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("SR-301", "EXT-201"), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("DEC-201", "EXT-201"), prefer="cooling")
        equilibrium_packets = _separation_packets(stream_table, unit_ids=("purification",), families=("extraction",))
    else:
        process_packet = _unit_operation_packet(stream_table, unit_ids=("purification",), unit_types=("distillation", "evaporation"))
        heating_packet = _thermal_packet(energy_balance, unit_ids=("D-101", "EV-101"), prefer="heating")
        cooling_packet = _thermal_packet(energy_balance, unit_ids=("D-101", "V-101", "E-201"), prefer="cooling")
        equilibrium_packets = _separation_packets(stream_table, unit_ids=("purification", "concentration"), families=("distillation", "evaporation"))
    if not equilibrium_packets:
        equilibrium_packets = [
            packet
            for packet in stream_table.separation_packets
            if packet.equilibrium_model in {"henry_law", "heuristic_gle_fallback", "solubility_curve", "heuristic_sle_fallback"}
            or packet.separation_family in {"absorption", "stripping", "crystallization", "filtration", "drying", "extraction"}
        ]
    process_state = composition_state_for_unit(
        stream_table.composition_states,
        unit_ids=("purification", "concentration", "regeneration", "filtration", "drying"),
        unit_types=("distillation", "evaporation", "stripping", "filtration", "drying", "extraction"),
    )
    process_mixture = mixture_package_for_state(
        process_state,
        mixture_properties,
        unit_ids=("purification", "concentration", "regeneration", "filtration", "drying"),
    )
    process_density = process_mixture.liquid_density_kg_m3 if process_mixture and process_mixture.liquid_density_kg_m3 else 950.0
    process_viscosity = process_mixture.liquid_viscosity_pa_s if process_mixture and process_mixture.liquid_viscosity_pa_s else 0.0018
    process_cp = process_mixture.liquid_heat_capacity_kj_kg_k if process_mixture and process_mixture.liquid_heat_capacity_kj_kg_k else 2.5
    product_mass = (
        max(process_packet.outlet_mass_flow_kg_hr * 0.72, _product_mass(stream_table))
        if process_packet is not None and process_packet.outlet_mass_flow_kg_hr > 0.0
        else _product_mass(stream_table)
    )
    target_purity = min(max(basis.target_purity_wt_pct / 100.0, 0.85), 0.999)
    packet_families = {packet.separation_family for packet in equilibrium_packets}
    is_absorption_family = "absorption" in separation_type or bool(packet_families & {"absorption", "stripping"})
    is_crystallization_family = ("crystallization" in separation_type or "filtration" in separation_type) or bool(packet_families & {"crystallization", "filtration", "drying"})
    is_extraction_family = "extraction" in separation_type or "extraction" in packet_families
    if is_absorption_family:
        service = "Absorption tower train"
        light_key = "Offgas"
        heavy_key = "Rich absorbent"
        alpha = 1.08
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.18, 1200.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.45, 1800.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 55.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 98.0
    elif is_crystallization_family:
        service = "Crystallizer / filtration / dryer equivalent train"
        light_key = "Mother liquor"
        heavy_key = "Crystal product"
        alpha = 1.02
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.30, 900.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.30, 900.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 45.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 110.0
    elif is_extraction_family:
        service = "Extraction and solvent recovery train"
        light_key = "Solvent-rich phase"
        heavy_key = "Product-rich phase"
        alpha = 1.15
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
        reboiler = max(heating_packet.heating_kw if heating_packet else energy_balance.total_heating_kw * 0.55, 1200.0)
        condenser = max(cooling_packet.cooling_kw if cooling_packet else energy_balance.total_cooling_kw * 0.50, 1100.0)
        top_temp = cooling_packet.hot_target_temp_c if cooling_packet else 92.0
        bottom_temp = heating_packet.cold_target_temp_c if heating_packet else 198.0
    vle_alpha_top = 0.0
    vle_alpha_bottom = 0.0
    vle_method = "route_family_proxy"
    if separation_thermo is not None and separation_thermo.relative_volatility is not None:
        if separation_thermo.light_key:
            light_key = separation_thermo.light_key
        if separation_thermo.heavy_key:
            heavy_key = separation_thermo.heavy_key
        if separation_thermo.relative_volatility.average_alpha > 1.0:
            alpha = separation_thermo.relative_volatility.average_alpha
        top_temp = separation_thermo.nominal_top_temp_c or top_temp
        bottom_temp = separation_thermo.nominal_bottom_temp_c or bottom_temp
        vle_alpha_top = separation_thermo.relative_volatility.top_alpha
        vle_alpha_bottom = separation_thermo.relative_volatility.bottom_alpha
        vle_method = separation_thermo.relative_volatility.method
    process_unit_ids = ("purification", "concentration", "regeneration", "drying", "filtration")
    heating_train_steps = _train_steps_for_units(utility_architecture, sink_unit_ids=process_unit_ids)
    condenser_train_steps = _train_steps_for_units(utility_architecture, source_unit_ids=process_unit_ids)
    heat_stream_lookup = _heat_stream_lookup(utility_architecture)
    reboiler_package = _select_package_item(heating_train_steps, role="exchanger", family="reboiler")
    condenser_package = _select_package_item(condenser_train_steps, role="exchanger", family="condenser")
    top_pressure_bar = max(route.operating_pressure_bar * 0.18, 1.2) if "distillation" in service.lower() else max(route.operating_pressure_bar * 0.45, 1.3)
    average_mw = _average_molecular_weight_g_mol(process_state, side="outlet", default=32.0)
    vapor_density = max((top_pressure_bar * 1.0e5) * (average_mw / 1000.0) / (8.314 * max(top_temp + 273.15, 250.0)), 0.35)
    xD_lk = min(max(0.985 if "distillation" in service.lower() else 0.94, 0.80), 0.999)
    xB_lk = min(max(1.0 - target_purity, 0.004), 0.12)
    xB_hk = min(max(target_purity, 0.88), 0.999)
    xD_hk = min(max(1.0 - xD_lk, 0.0015), 0.10)
    q_factor = min(max(1.0 + (process_cp * max(bottom_temp - top_temp, 15.0)) / 2200.0, 0.85), 1.35)
    min_stages = _fenske_min_stages(alpha, xD_lk, xB_lk, xD_hk, xB_hk) if alpha > 1.03 else (6.0 if "absorption" in service.lower() else 3.0)
    min_reflux = _underwood_min_reflux_proxy(alpha, q_factor, xD_lk) if "distillation" in service.lower() else (0.16 if "absorption" in service.lower() else 0.08 if "crystallizer" in service.lower() else 0.24)
    reflux = max(
        min_reflux * (1.32 if "distillation" in service.lower() else 1.20 if "absorption" in service.lower() else 1.12),
        0.12 if "crystallizer" in service.lower() else 0.20,
    )
    theoretical_stages = _gilliland_actual_stages_proxy(min_stages, min_reflux, reflux) if alpha > 1.03 else max(min_stages * 1.18, min_stages + 1.0)
    tray_efficiency = _tray_efficiency_proxy(process_viscosity, alpha, service)
    stages = max(int(math.ceil(theoretical_stages / max(tray_efficiency, 0.35))), 4 if "crystallizer" in service.lower() else 6)
    reboiler_phase_change_load = reboiler_package.phase_change_load_kg_hr if reboiler_package is not None and reboiler_package.phase_change_load_kg_hr > 0.0 else _latent_load_kg_hr(reboiler, 1850.0)
    condenser_phase_change_load = condenser_package.phase_change_load_kg_hr if condenser_package is not None and condenser_package.phase_change_load_kg_hr > 0.0 else _latent_load_kg_hr(condenser, 2100.0)
    distillate_mass = max(condenser_phase_change_load / max(reflux + 1.0, 1.0), product_mass * (0.12 if "distillation" in service.lower() else 0.08))
    liquid_load_m3_hr = max((distillate_mass * (1.0 + reflux)) / max(process_density, 1.0), 0.6)
    vapor_flow_m3_hr = max(reboiler_phase_change_load / max(vapor_density, 0.1), 1.0)
    tray_spacing = 0.45 if "distillation" in service.lower() else 0.55 if "absorption" in service.lower() else 0.60
    capacity_factor = (0.30 if "distillation" in service.lower() else 0.24 if "absorption" in service.lower() else 0.18) * math.sqrt(max(tray_spacing / 0.45, 0.8))
    allowable_vapor_velocity = max(capacity_factor * math.sqrt(max((process_density - vapor_density) / max(vapor_density, 0.05), 0.2)), 0.35)
    target_flooding = 0.74 if "distillation" in service.lower() else 0.68 if "absorption" in service.lower() else 0.55
    active_area = max((vapor_flow_m3_hr / 3600.0) / max(allowable_vapor_velocity * target_flooding, 0.05), 0.5)
    downcomer_fraction = 0.14 if "distillation" in service.lower() else 0.12 if "absorption" in service.lower() else 0.08
    diameter = max(math.sqrt((4.0 * active_area) / (math.pi * max(1.0 - downcomer_fraction, 0.25))), 1.2 if "crystallizer" in service.lower() else 1.5)
    superficial_vapor_velocity = max((vapor_flow_m3_hr / 3600.0) / max((math.pi * (diameter / 2.0) ** 2) * max(1.0 - downcomer_fraction, 0.25), 1e-6), 0.1)
    flooding_fraction = min(max(superficial_vapor_velocity / max(allowable_vapor_velocity, 0.1), 0.35), 0.88)
    pressure_drop_per_stage = 0.16 + 0.22 * flooding_fraction + 0.02 * reflux
    height = max(stages * tray_spacing + 3.5, 8.0 if "crystallizer" in service.lower() else 12.0)
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
    equilibrium_models = sorted({packet.equilibrium_model for packet in equilibrium_packets if packet.equilibrium_model})
    equilibrium_parameter_ids = sorted({parameter_id for packet in equilibrium_packets for parameter_id in packet.equilibrium_parameter_ids})
    equilibrium_fallback = any(packet.equilibrium_fallback for packet in equilibrium_packets)
    equilibrium_notes = sorted({note for packet in equilibrium_packets for note in packet.notes if note})
    absorber_key_component = ""
    absorber_henry_constant_bar = 0.0
    absorber_equilibrium_slope = 0.0
    absorber_solvent_to_gas_ratio = 0.0
    absorber_capture_fraction = 0.0
    absorber_stage_efficiency = 0.0
    absorber_theoretical_stages = 0.0
    absorber_packed_height_m = 0.0
    absorber_gas_mass_velocity_kg_m2_s = 0.0
    absorber_liquid_mass_velocity_kg_m2_s = 0.0
    absorber_ntu = 0.0
    absorber_htu_m = 0.0
    absorber_overall_mass_transfer_coefficient_1_s = 0.0
    absorber_packing_family = ""
    absorber_packing_specific_area_m2_m3 = 0.0
    absorber_effective_interfacial_area_m2_m3 = 0.0
    absorber_gas_phase_transfer_coeff_1_s = 0.0
    absorber_liquid_phase_transfer_coeff_1_s = 0.0
    absorber_min_wetting_rate_kg_m2_s = 0.0
    absorber_wetting_ratio = 0.0
    absorber_operating_velocity_m_s = 0.0
    absorber_flooding_velocity_m_s = 0.0
    absorber_flooding_margin_fraction = 0.0
    absorber_pressure_drop_per_m_kpa_m = 0.0
    absorber_total_pressure_drop_kpa = 0.0
    crystallizer_key_component = ""
    crystallizer_solubility_limit_kg_per_kg = 0.0
    crystallizer_feed_loading_kg_per_kg = 0.0
    crystallizer_supersaturation_ratio = 0.0
    crystallizer_precipitated_mass_kg_hr = 0.0
    crystallizer_dissolved_mass_kg_hr = 0.0
    crystallizer_yield_fraction = 0.0
    crystallizer_residence_time_hr = 0.0
    crystallizer_holdup_m3 = 0.0
    crystal_slurry_density_kg_m3 = 0.0
    crystal_growth_rate_mm_hr = 0.0
    crystal_size_d10_mm = 0.0
    crystal_size_d50_mm = 0.0
    crystal_size_d90_mm = 0.0
    crystal_classifier_cut_size_mm = 0.0
    crystal_classified_product_fraction = 0.0
    slurry_circulation_rate_m3_hr = 0.0
    filter_cake_moisture_fraction = 0.0
    filter_area_m2 = 0.0
    filter_cake_throughput_kg_m2_hr = 0.0
    filter_specific_cake_resistance_m_kg = 0.0
    filter_medium_resistance_1_m = 0.0
    dryer_evaporation_load_kg_hr = 0.0
    dryer_residence_time_hr = 0.0
    dryer_target_moisture_fraction = 0.0
    dryer_product_moisture_fraction = 0.0
    dryer_equilibrium_moisture_fraction = 0.0
    dryer_inlet_humidity_ratio_kg_kg = 0.0
    dryer_exhaust_humidity_ratio_kg_kg = 0.0
    dryer_dry_air_flow_kg_hr = 0.0
    dryer_exhaust_saturation_fraction = 0.0
    dryer_mass_transfer_coefficient_kg_m2_s = 0.0
    dryer_heat_transfer_coefficient_w_m2_k = 0.0
    dryer_heat_transfer_area_m2 = 0.0
    dryer_refined_duty_kw = 0.0
    traces = [
        CalcTrace(trace_id="process_unit_service", title="Process-unit family", formula="service = selected separation family", result=service, units=""),
        CalcTrace(
            trace_id="column_vle_basis",
            title="Separation thermodynamics basis",
            formula="alpha = sqrt(alpha_top * alpha_bottom) from component K-values when a VLE basis exists",
            substitutions={
                "light_key": light_key,
                "heavy_key": heavy_key,
                "alpha_top": f"{vle_alpha_top:.4f}" if vle_alpha_top > 0.0 else "fallback",
                "alpha_bottom": f"{vle_alpha_bottom:.4f}" if vle_alpha_bottom > 0.0 else "fallback",
                "method": vle_method,
            },
            result=f"{alpha:.4f}",
            units="-",
            notes="Column volatility basis now prefers the separation-thermodynamics artifact built from Antoine / Clausius-Clapeyron K-values when available.",
        ),
        CalcTrace(
            trace_id="column_fenske_min_stages",
            title="Minimum theoretical stages",
            formula="Nmin = log[(xD,LK/xB,LK)*(xB,HK/xD,HK)] / log(alpha)",
            substitutions={
                "xD,LK": f"{xD_lk:.4f}",
                "xB,LK": f"{xB_lk:.4f}",
                "xD,HK": f"{xD_hk:.4f}",
                "xB,HK": f"{xB_hk:.4f}",
                "alpha": f"{alpha:.3f}",
            },
            result=f"{min_stages:.3f}",
            units="stages",
        ),
        CalcTrace(
            trace_id="column_underwood_min_reflux",
            title="Minimum reflux proxy",
            formula="Rmin = f(alpha, q, xD,LK)",
            substitutions={"alpha": f"{alpha:.3f}", "q": f"{q_factor:.3f}", "xD,LK": f"{xD_lk:.4f}"},
            result=f"{min_reflux:.3f}",
            units="-",
            notes="This is a screening Underwood-style reflux estimate built from the solved property basis and separation severity.",
        ),
        CalcTrace(
            trace_id="column_gilliland_actual_stages",
            title="Actual stage proxy",
            formula="Nactual = g(Nmin, R/Rmin, tray efficiency)",
            substitutions={
                "Nmin": f"{min_stages:.3f}",
                "R": f"{reflux:.3f}",
                "Rmin": f"{min_reflux:.3f}",
                "tray_eff": f"{tray_efficiency:.3f}",
            },
            result=f"{stages:.3f}",
            units="actual stages",
        ),
        CalcTrace(trace_id="process_unit_size", title="Equivalent diameter", formula="D = sqrt(4*Aactive/[pi*(1-Adc)])", substitutions={"Aactive": f"{active_area:.3f}", "Adc": f"{downcomer_fraction:.3f}"}, result=f"{diameter:.3f}", units="m"),
        CalcTrace(
            trace_id="process_unit_hydraulics_capacity",
            title="Column hydraulic capacity basis",
            formula="uallow = C * sqrt[(rhoL-rhoV)/rhoV]; uflood = usuperficial/uallow",
            substitutions={
                "C": f"{capacity_factor:.3f}",
                "rhoL": f"{process_density:.3f}",
                "rhoV": f"{vapor_density:.3f}",
                "usuperficial": f"{superficial_vapor_velocity:.3f}",
            },
            result=f"{flooding_fraction:.3f}",
            units="-",
        ),
        CalcTrace(
            trace_id="process_unit_property_basis",
            title="Process-unit property-package basis",
            formula="Hydraulics proxy uses density, viscosity, and Cp from the mixture-property package",
            substitutions={
                "density": f"{process_density:.3f}",
                "viscosity": f"{process_viscosity:.6f}",
                "Cp": f"{process_cp:.3f}",
                "mixture_package": process_mixture.mixture_id if process_mixture else "fallback",
            },
            result=f"{process_density:.3f}",
            units="kg/m3",
        ),
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
            trace_id="column_reboiler_package_basis",
            title="Reboiler package basis",
            formula="Vboil = Qreb / lambda; circulation from selected train package when available",
            substitutions={
                "package": reboiler_package.package_item_id if reboiler_package is not None else "fallback",
                "package_type": reboiler_package.equipment_type if reboiler_package is not None else "generic",
                "phase_change_load_kg_hr": f"{reboiler_phase_change_load:.3f}",
                "circulation_ratio": f"{reboiler_package.circulation_ratio if reboiler_package is not None else 3.0:.3f}",
            },
            result=f"{reboiler:.3f}",
            units="kW",
        ),
        CalcTrace(
            trace_id="column_condenser_package_basis",
            title="Condenser package basis",
            formula="mcond = Qcond / lambda; circulation from selected train package when available",
            substitutions={
                "package": condenser_package.package_item_id if condenser_package is not None else "fallback",
                "package_type": condenser_package.equipment_type if condenser_package is not None else "generic",
                "phase_change_load_kg_hr": f"{condenser_phase_change_load:.3f}",
                "circulation_flow_m3_hr": f"{condenser_package.flow_m3_hr if condenser_package is not None else liquid_load_m3_hr:.3f}",
            },
            result=f"{condenser:.3f}",
            units="kW",
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
    if equilibrium_packets:
        traces.append(
            CalcTrace(
                trace_id="process_unit_equilibrium_packet_basis",
                title="Solved equilibrium packet basis",
                formula="selected separation packets provide the active phase-equilibrium model and split basis for this process-unit family",
                substitutions={
                    "packet_ids": ", ".join(packet.packet_id for packet in equilibrium_packets),
                    "models": ", ".join(equilibrium_models) or "heuristic",
                    "parameter_ids": ", ".join(equilibrium_parameter_ids) or "none",
                    "fallback": "yes" if equilibrium_fallback else "no",
                },
                result=", ".join(equilibrium_models) or "heuristic_split",
                units="",
                notes="This basis is consumed directly from the solved separator packets rather than being inferred from chapter prose.",
            )
        )
    if is_absorption_family and equilibrium_packets:
        absorber_packet = next(
            (packet for packet in equilibrium_packets if packet.unit_id == "primary_separation"),
            equilibrium_packets[0],
        )
        absorbed_component = _preferred_equilibrium_component(absorber_packet, mode="gle")
        if absorbed_component:
            absorber_key_component = absorbed_component
            retained_fraction = min(
                absorber_packet.component_split_to_product.get(absorbed_component, 0.0)
                + absorber_packet.component_split_to_recycle.get(absorbed_component, 0.0),
                1.0,
            )
            absorber_capture_fraction = retained_fraction
            overhead_fraction = absorber_packet.component_split_to_waste.get(absorbed_component, 0.0)
            absorbed_mass = (
                _stream_component_mass_kg_hr(stream_table, absorber_packet.product_stream_ids, absorbed_component)
                + _stream_component_mass_kg_hr(stream_table, absorber_packet.recycle_stream_ids, absorbed_component)
            )
            overhead_mass = _stream_component_mass_kg_hr(stream_table, absorber_packet.waste_stream_ids, absorbed_component)
            inlet_gas_molar = _stream_component_molar_kmol_hr(stream_table, absorber_packet.inlet_stream_ids, absorbed_component)
            inlet_components = {
                component.name
                for stream in stream_table.streams
                if stream.stream_id in set(absorber_packet.inlet_stream_ids)
                for component in stream.components
            }
            solvent_candidates = [
                name
                for name in sorted(inlet_components)
                if normalize_chemical_name(name) in {"water", "sulfuric_acid", "spent_acid"}
            ]
            solvent_name = next(
                (
                    candidate
                    for candidate in solvent_candidates
                    if _lookup_henry_constant(property_packages, absorbed_component, candidate) is not None
                ),
                solvent_candidates[0] if solvent_candidates else "",
            )
            solvent_molar = _stream_component_molar_kmol_hr(stream_table, absorber_packet.inlet_stream_ids, solvent_name) if solvent_name else 0.0
            absorber_solvent_to_gas_ratio = solvent_molar / max(inlet_gas_molar, 1e-9) if solvent_molar > 0.0 else 0.0
            henry_constant = _lookup_henry_constant(property_packages, absorbed_component, solvent_name) if solvent_name else None
            if henry_constant is not None:
                absorber_henry_constant_bar = henry_constant.value
                absorber_equilibrium_slope = absorber_henry_constant_bar / max(max(route.operating_pressure_bar - 0.8, 1.0), 1e-6)
            elif retained_fraction > 0.0:
                absorber_equilibrium_slope = max(1.0 / retained_fraction, 1.0)
            absorption_factor = absorber_solvent_to_gas_ratio / max(absorber_equilibrium_slope, 1e-6) if absorber_equilibrium_slope > 0.0 else 0.0
            if absorption_factor > 1.02 and 0.0 < retained_fraction < 0.9995:
                absorber_theoretical_stages = max(
                    math.log(1.0 / max(1.0 - retained_fraction, 1e-6)) / math.log(absorption_factor),
                    1.0,
                )
            else:
                absorber_theoretical_stages = max(2.0, 5.0 * retained_fraction)
            absorber_stage_efficiency = min(max(0.52 + 0.10 * min(absorption_factor, 3.0) / 3.0, 0.45), 0.78)
            solvent_mass_flow = _stream_total_mass_kg_hr(stream_table, absorber_packet.product_stream_ids + absorber_packet.recycle_stream_ids)
            gas_mass_flow = _stream_total_mass_kg_hr(stream_table, absorber_packet.waste_stream_ids)
            absorber_gas_mass_velocity_kg_m2_s = gas_mass_flow / max(active_area * 3600.0, 1e-9)
            absorber_liquid_mass_velocity_kg_m2_s = solvent_mass_flow / max(active_area * 3600.0, 1e-9)
            gas_superficial_velocity = absorber_gas_mass_velocity_kg_m2_s / max(vapor_density, 0.1)
            liquid_superficial_velocity = absorber_liquid_mass_velocity_kg_m2_s / max(process_density, 1.0)
            viscosity_ratio = min(max(process_viscosity / 0.0025, 0.4), 4.0)
            if process_viscosity <= 0.0025 and diameter >= 1.6:
                absorber_packing_family = "structured_250y"
                absorber_packing_specific_area_m2_m3 = 250.0
            else:
                absorber_packing_family = "random_50mm_pall"
                absorber_packing_specific_area_m2_m3 = 125.0
            absorber_operating_velocity_m_s = gas_superficial_velocity
            absorber_flooding_velocity_m_s = max(
                allowable_vapor_velocity * (1.08 if absorber_packing_family.startswith("structured") else 1.00),
                gas_superficial_velocity * 1.05,
            )
            absorber_flooding_margin_fraction = max(
                1.0 - absorber_operating_velocity_m_s / max(absorber_flooding_velocity_m_s, 1e-6),
                0.02,
            )
            absorber_min_wetting_rate_kg_m2_s = min(
                max(0.032 + 0.00009 * absorber_packing_specific_area_m2_m3 + 0.010 * min(viscosity_ratio, 3.0), 0.040),
                0.120,
            )
            absorber_wetting_ratio = absorber_liquid_mass_velocity_kg_m2_s / max(absorber_min_wetting_rate_kg_m2_s, 1e-6)
            wetted_fraction = min(
                max(
                    0.42
                    + 0.18 * min(absorber_wetting_ratio, 2.0) / 2.0
                    + 0.08 * min(liquid_superficial_velocity / 0.01, 2.0),
                    0.35,
                ),
                0.95,
            )
            absorber_effective_interfacial_area_m2_m3 = absorber_packing_specific_area_m2_m3 * wetted_fraction
            absorber_gas_phase_transfer_coeff_1_s = min(
                max(
                    0.030
                    + 0.095 * math.pow(max(gas_superficial_velocity, 0.02), 0.72)
                    * math.pow(max(absorber_packing_specific_area_m2_m3 / 125.0, 0.6), 0.22),
                    0.020,
                ),
                0.220,
            )
            absorber_liquid_phase_transfer_coeff_1_s = min(
                max(
                    0.012
                    + 0.055 * math.pow(max(liquid_superficial_velocity, 0.005), 0.60)
                    * math.pow(max(absorber_packing_specific_area_m2_m3 / 125.0, 0.6), 0.30)
                    / math.pow(max(viscosity_ratio, 0.5), 0.25),
                    0.010,
                ),
                0.180,
            )
            correlated_overall_coeff = 1.0 / max(
                (1.0 / max(absorber_gas_phase_transfer_coeff_1_s, 1e-6))
                + (1.0 / max(absorber_liquid_phase_transfer_coeff_1_s * max(absorption_factor, 0.65), 1e-6)),
                1e-6,
            )
            absorber_overall_mass_transfer_coefficient_1_s = min(
                max(
                    correlated_overall_coeff * max(absorber_effective_interfacial_area_m2_m3 / max(absorber_packing_specific_area_m2_m3, 1.0), 0.30),
                    0.030,
                ),
                0.75,
            )
            absorber_ntu = max(math.log(1.0 / max(1.0 - retained_fraction, 1e-6)), 0.35)
            absorber_htu_m = min(
                max(
                    gas_superficial_velocity
                    / max(
                        absorber_overall_mass_transfer_coefficient_1_s
                        * max(1.0 + 0.35 * max(absorption_factor - 1.0, 0.0), 1.0),
                        1e-6,
                    ),
                    0.30,
                ),
                1.75,
            )
            absorber_packed_height_m = max(absorber_htu_m * absorber_ntu * 1.15, 3.0)
            absorber_pressure_drop_per_m_kpa_m = min(
                max(
                    0.18
                    + (0.78 if absorber_packing_family.startswith("structured") else 0.95) * math.pow(max(absorber_gas_mass_velocity_kg_m2_s, 0.05), 1.15)
                    + 0.05 * absorber_liquid_mass_velocity_kg_m2_s
                    + 0.65 * max(absorber_operating_velocity_m_s / max(absorber_flooding_velocity_m_s, 1e-6) - 0.55, 0.0),
                    0.15,
                ),
                4.00,
            )
            absorber_total_pressure_drop_kpa = absorber_pressure_drop_per_m_kpa_m * absorber_packed_height_m
            theoretical_stages = max(theoretical_stages, absorber_theoretical_stages)
            tray_efficiency = max(tray_efficiency, absorber_stage_efficiency)
            stages = max(int(math.ceil(theoretical_stages / max(tray_efficiency, 0.35))), 6)
            height = max(height, absorber_packed_height_m + 3.5)
            traces.extend(
                [
                    CalcTrace(
                        trace_id="absorption_equilibrium_basis",
                        title="Absorber Henry-law basis",
                        formula="retained fraction = split_product + split_recycle = 1 - split_waste",
                        substitutions={
                            "unit_id": absorber_packet.unit_id,
                            "component": absorbed_component,
                            "model": absorber_packet.equilibrium_model or "heuristic_gle_fallback",
                            "parameter_ids": ", ".join(absorber_packet.equilibrium_parameter_ids) or "none",
                            "split_product": f"{absorber_packet.component_split_to_product.get(absorbed_component, 0.0):.4f}",
                            "split_recycle": f"{absorber_packet.component_split_to_recycle.get(absorbed_component, 0.0):.4f}",
                            "split_waste": f"{overhead_fraction:.4f}",
                        },
                        result=f"{retained_fraction:.4f}",
                        units="-",
                        notes=(
                            "GLE basis falls back to heuristic partitioning when cited Henry-law constants are unavailable."
                            if absorber_packet.equilibrium_fallback
                            else "GLE capture basis comes from the solved Henry-law separation packet."
                        ),
                    ),
                    CalcTrace(
                        trace_id="absorption_component_capture",
                        title="Absorbed component capture basis",
                        formula="m_captured = m_product + m_recycle; m_offgas = m_waste",
                        substitutions={
                            "component": absorbed_component,
                            "m_product": f"{_stream_component_mass_kg_hr(stream_table, absorber_packet.product_stream_ids, absorbed_component):.3f}",
                            "m_recycle": f"{_stream_component_mass_kg_hr(stream_table, absorber_packet.recycle_stream_ids, absorbed_component):.3f}",
                            "m_waste": f"{overhead_mass:.3f}",
                        },
                        result=f"{absorbed_mass:.3f}",
                        units="kg/h",
                        notes="This exposes the captured gas mass basis used by the absorber/regeneration train in the solved flowsheet.",
                    ),
                    CalcTrace(
                        trace_id="absorption_factor_screening",
                        title="Absorber stage-screening basis",
                        formula="A = (L/V)/m ; Nscreen = ln[1/(1-capture)] / ln(A) for A > 1",
                        substitutions={
                            "component": absorbed_component,
                            "L/V": f"{absorber_solvent_to_gas_ratio:.4f}",
                            "m": f"{absorber_equilibrium_slope:.4f}",
                            "A": f"{absorption_factor:.4f}",
                            "capture": f"{retained_fraction:.4f}",
                        },
                        result=f"{absorber_theoretical_stages:.3f}",
                        units="stages",
                        notes="This is a Kremser-style screening estimate anchored to the solved Henry-law capture basis.",
                    ),
                    CalcTrace(
                        trace_id="absorption_packed_height_basis",
                        title="Absorber packed-height basis",
                        formula="H = (Nscreen / efficiency) * HETP",
                        substitutions={
                            "Nscreen": f"{absorber_theoretical_stages:.3f}",
                            "efficiency": f"{absorber_stage_efficiency:.3f}",
                            "HETP": "0.75",
                        },
                        result=f"{absorber_packed_height_m:.3f}",
                        units="m",
                        notes="Packed height is a screening basis for the absorber and not a detailed packing-vendor design.",
                    ),
                    CalcTrace(
                        trace_id="absorption_mass_transfer_hydraulics",
                        title="Packed-tower mass-transfer screening",
                        formula="HTU/NTU basis with gas and liquid mass velocities over active packing area",
                        substitutions={
                            "gas_mass_velocity": f"{absorber_gas_mass_velocity_kg_m2_s:.4f}",
                            "liquid_mass_velocity": f"{absorber_liquid_mass_velocity_kg_m2_s:.4f}",
                            "packing_family": absorber_packing_family,
                            "aeff": f"{absorber_effective_interfacial_area_m2_m3:.2f}",
                            "KGa": f"{absorber_overall_mass_transfer_coefficient_1_s:.4f}",
                            "NTU": f"{absorber_ntu:.4f}",
                            "HTU": f"{absorber_htu_m:.4f}",
                        },
                        result=f"{absorber_packed_height_m:.3f}",
                        units="m packed height",
                        notes="This is the packed-tower hydraulic/mass-transfer screening layer built on top of the Henry-law capture basis.",
                    ),
                    CalcTrace(
                        trace_id="absorption_pressure_drop_basis",
                        title="Packed-tower pressure-drop basis",
                        formula="dP/dz = f(G, L, flooding); dPtotal = (dP/dz) * Hpacked",
                        substitutions={
                            "G": f"{absorber_gas_mass_velocity_kg_m2_s:.4f}",
                            "L": f"{absorber_liquid_mass_velocity_kg_m2_s:.4f}",
                            "flooding_fraction": f"{flooding_fraction:.4f}",
                            "Hpacked": f"{absorber_packed_height_m:.4f}",
                        },
                        result=f"{absorber_total_pressure_drop_kpa:.3f}",
                        units="kPa",
                        notes="Pressure-drop screening is used to keep the packed absorber inside a feasible hydraulic envelope.",
                    ),
                    CalcTrace(
                        trace_id="absorption_transfer_unit_family_basis",
                        title="Packing-family transfer-unit basis",
                        formula="KGa uses packing-family specific area and gas/liquid film coefficients",
                        substitutions={
                            "packing_family": absorber_packing_family,
                            "a_spec": f"{absorber_packing_specific_area_m2_m3:.1f}",
                            "a_eff": f"{absorber_effective_interfacial_area_m2_m3:.1f}",
                            "kG": f"{absorber_gas_phase_transfer_coeff_1_s:.4f}",
                            "kL": f"{absorber_liquid_phase_transfer_coeff_1_s:.4f}",
                        },
                        result=f"{absorber_overall_mass_transfer_coefficient_1_s:.4f}",
                        units="1/s",
                        notes="This upgrades the absorber basis from one generic coefficient to a packing-family transport screening.",
                    ),
                    CalcTrace(
                        trace_id="absorption_packed_bed_window",
                        title="Packed-bed wetting and flooding window",
                        formula="wetting ratio = L/Lmin ; flooding margin = 1 - uop/uflood",
                        substitutions={
                            "L": f"{absorber_liquid_mass_velocity_kg_m2_s:.4f}",
                            "Lmin": f"{absorber_min_wetting_rate_kg_m2_s:.4f}",
                            "uop": f"{absorber_operating_velocity_m_s:.4f}",
                            "uflood": f"{absorber_flooding_velocity_m_s:.4f}",
                        },
                        result=f"{absorber_flooding_margin_fraction:.4f}",
                        units="fraction margin",
                        notes="This checks that the packed column is operating above a wetting threshold and below the flooding window.",
                    ),
                ]
            )
    if is_crystallization_family and equilibrium_packets:
        crystal_packet = next(
            (
                packet
                for packet in equilibrium_packets
                if packet.unit_id in {"concentration", "filtration"} and packet.equilibrium_model in {"solubility_curve", "heuristic_sle_fallback"}
            ),
            equilibrium_packets[0],
        )
        crystal_component = _preferred_equilibrium_component(crystal_packet, mode="sle")
        if crystal_component:
            crystallizer_key_component = crystal_component
            precipitated_mass = _stream_component_mass_kg_hr(stream_table, crystal_packet.product_stream_ids, crystal_component)
            dissolved_mass = (
                _stream_component_mass_kg_hr(stream_table, crystal_packet.recycle_stream_ids, crystal_component)
                + _stream_component_mass_kg_hr(stream_table, crystal_packet.waste_stream_ids, crystal_component)
            )
            crystallizer_precipitated_mass_kg_hr = precipitated_mass
            crystallizer_dissolved_mass_kg_hr = dissolved_mass
            crystal_yield = precipitated_mass / max(precipitated_mass + dissolved_mass, 1e-9)
            crystallizer_yield_fraction = crystal_yield
            solvent_name = "Water"
            crystal_temperature_c = _average_stream_temperature_c(
                stream_table,
                crystal_packet.product_stream_ids + crystal_packet.recycle_stream_ids + crystal_packet.waste_stream_ids,
                top_temp or 35.0,
            )
            solubility_curve = _lookup_solubility_curve(property_packages, crystal_component, solvent_name)
            solubility_limit = _evaluate_solubility_curve(solubility_curve, crystal_temperature_c)
            solvent_mass_in = _stream_component_mass_kg_hr(stream_table, crystal_packet.inlet_stream_ids, solvent_name)
            solute_mass_in = _stream_component_mass_kg_hr(stream_table, crystal_packet.inlet_stream_ids, crystal_component)
            if solvent_mass_in > 0.0:
                crystallizer_feed_loading_kg_per_kg = solute_mass_in / solvent_mass_in
            if solubility_limit is not None:
                crystallizer_solubility_limit_kg_per_kg = solubility_limit
                crystallizer_supersaturation_ratio = crystallizer_feed_loading_kg_per_kg / max(solubility_limit, 1e-9)
            wet_cake_mass = _stream_total_mass_kg_hr(stream_table, crystal_packet.product_stream_ids)
            wet_cake_water_mass = _stream_component_mass_kg_hr(stream_table, crystal_packet.product_stream_ids, "Water")
            filter_cake_moisture_fraction = wet_cake_water_mass / max(wet_cake_mass, 1e-9)
            filtrate_mass = _stream_total_mass_kg_hr(stream_table, crystal_packet.recycle_stream_ids + crystal_packet.waste_stream_ids)
            filter_flux_m3_m2_hr = 0.18 if crystallizer_supersaturation_ratio > 1.20 else 0.24
            filter_area_m2 = max((filtrate_mass / max(process_density, 1.0)) / max(filter_flux_m3_m2_hr, 1e-6), 1.0)
            filter_cake_throughput_kg_m2_hr = wet_cake_mass / max(filter_area_m2, 1e-9)
            crystal_slurry_density_kg_m3 = max(process_density * (1.05 + 0.10 * min(crystallizer_supersaturation_ratio, 2.0)), process_density)
            crystal_growth_rate_mm_hr = min(
                max(0.10 + 0.65 * math.pow(max(crystallizer_supersaturation_ratio - 1.0, 0.0), 1.10), 0.05),
                2.00,
            )
            target_crystal_size_mm = min(max(0.35 + 0.18 * max(crystallizer_supersaturation_ratio - 1.0, 0.0), 0.25), 0.90)
            crystal_size_d50_mm = target_crystal_size_mm
            crystal_size_d10_mm = max(target_crystal_size_mm * (0.48 + 0.04 * min(crystallizer_supersaturation_ratio, 2.5)), 0.08)
            crystal_size_d90_mm = max(target_crystal_size_mm * (1.55 + 0.08 * min(crystallizer_supersaturation_ratio, 2.5)), crystal_size_d50_mm)
            crystal_classifier_cut_size_mm = max(min(0.72 * crystal_size_d50_mm, crystal_size_d50_mm), 0.08)
            classification_span = max(crystal_size_d90_mm - crystal_size_d10_mm, 0.05)
            crystal_classified_product_fraction = min(
                max(0.55 + 0.35 * (crystal_size_d50_mm - crystal_classifier_cut_size_mm) / classification_span, 0.25),
                0.97,
            )
            crystallizer_residence_time_hr = min(max(target_crystal_size_mm / max(crystal_growth_rate_mm_hr, 0.05), 0.8), 4.5)
            slurry_mass_flow = wet_cake_mass + filtrate_mass
            slurry_volumetric_flow_m3_hr = slurry_mass_flow / max(crystal_slurry_density_kg_m3, 1.0)
            slurry_circulation_factor = min(max(2.5 + 1.4 * max(crystallizer_supersaturation_ratio - 1.0, 0.0), 2.0), 6.0)
            slurry_circulation_rate_m3_hr = slurry_volumetric_flow_m3_hr * slurry_circulation_factor
            crystallizer_holdup_m3 = slurry_volumetric_flow_m3_hr * crystallizer_residence_time_hr
            drying_packet = _unit_operation_packet(stream_table, unit_ids=("drying",), unit_types=("drying",))
            dry_crystal_mass = max(wet_cake_mass - wet_cake_water_mass, 0.0)
            crystal_porosity = min(max(0.42 - 0.05 * min(max(crystallizer_supersaturation_ratio - 1.0, 0.0), 1.8), 0.28), 0.48)
            particle_size_m = max(crystal_size_d50_mm / 1000.0, 5e-5)
            particle_density_kg_m3 = max(process_density * 1.35, 1400.0)
            filter_specific_cake_resistance_m_kg = min(
                max(
                    180.0
                    * max(1.0 - crystal_porosity, 0.05)
                    / max(particle_density_kg_m3 * math.pow(particle_size_m, 2) * math.pow(max(crystal_porosity, 0.20), 3), 1e-9),
                    5.0e6,
                ),
                2.0e10,
            )
            filter_medium_resistance_1_m = min(
                max(2.5e8 * (1.0 + 1.5 * filter_cake_moisture_fraction), 1.0e8),
                5.0e9,
            )
            dryer_target_moisture_fraction = min(max(0.012 + 0.020 * max(filter_cake_moisture_fraction - 0.08, 0.0), 0.010), 0.050)
            dryer_equilibrium_moisture_fraction = max(min(dryer_target_moisture_fraction * 0.55, dryer_target_moisture_fraction * 0.90), 0.004)
            target_product_water = (
                dry_crystal_mass * dryer_target_moisture_fraction / max(1.0 - dryer_target_moisture_fraction, 1e-6)
                if dry_crystal_mass > 0.0
                else 0.0
            )
            design_product_water = target_product_water
            if drying_packet is not None:
                dryer_feed_water = _stream_component_mass_kg_hr(stream_table, drying_packet.inlet_stream_ids, "Water")
                dryer_product_water = _stream_component_mass_kg_hr(stream_table, drying_packet.outlet_stream_ids, "Water")
                design_product_water = min(dryer_product_water, target_product_water) if dryer_product_water > 0.0 else target_product_water
            dryer_feed_water = wet_cake_water_mass if drying_packet is None else _stream_component_mass_kg_hr(stream_table, drying_packet.inlet_stream_ids, "Water")
            dryer_product_moisture_fraction = design_product_water / max(dry_crystal_mass + design_product_water, 1e-9)
            dryer_evaporation_load_kg_hr = max(dryer_feed_water - design_product_water, 0.0)
            dryer_residence_time_hr = min(
                max(
                    0.40
                    + 7.5 * max(filter_cake_moisture_fraction - dryer_product_moisture_fraction, 0.0)
                    + 0.08 * max(target_crystal_size_mm - 0.30, 0.0),
                    0.35,
                ),
                2.10,
            )
            latent_kw = dryer_evaporation_load_kg_hr * 2257.0 / 3600.0
            sensible_kw = dry_crystal_mass * 0.90 * max(85.0 - crystal_temperature_c, 20.0) / 3600.0
            endpoint_polish_kw = max(dryer_target_moisture_fraction - dryer_product_moisture_fraction, 0.0) * dry_crystal_mass * 120.0 / 3600.0
            dryer_refined_duty_kw = max(latent_kw + sensible_kw, heating_packet.heating_kw if heating_packet is not None else 0.0)
            dryer_refined_duty_kw += endpoint_polish_kw
            dryer_heat_transfer_coefficient_w_m2_k = min(
                max(42.0 + 18.0 * min(filter_cake_moisture_fraction / 0.15, 2.5) + 6.0 * min(dryer_residence_time_hr, 2.0), 35.0),
                140.0,
            )
            dryer_effective_delta_t_k = max(95.0 - crystal_temperature_c, 18.0)
            dryer_heat_transfer_area_m2 = max(
                (dryer_refined_duty_kw * 1000.0) / max(dryer_heat_transfer_coefficient_w_m2_k * dryer_effective_delta_t_k, 1.0),
                0.5,
            )
            moisture_driving_force = max(filter_cake_moisture_fraction - dryer_equilibrium_moisture_fraction, 0.01)
            dryer_inlet_humidity_ratio_kg_kg = 0.010
            saturation_humidity_capacity = min(max(0.090 + 0.0010 * max(85.0 - crystal_temperature_c, 15.0), 0.075), 0.180)
            target_exhaust_humidity = min(max(dryer_inlet_humidity_ratio_kg_kg + 0.060, 0.045), 0.82 * saturation_humidity_capacity)
            dryer_dry_air_flow_kg_hr = max(
                dryer_evaporation_load_kg_hr / max(target_exhaust_humidity - dryer_inlet_humidity_ratio_kg_kg, 0.01),
                200.0,
            )
            dryer_exhaust_humidity_ratio_kg_kg = dryer_inlet_humidity_ratio_kg_kg + dryer_evaporation_load_kg_hr / max(dryer_dry_air_flow_kg_hr, 1e-6)
            dryer_exhaust_saturation_fraction = min(
                max(dryer_exhaust_humidity_ratio_kg_kg / max(saturation_humidity_capacity, 1e-6), 0.05),
                0.98,
            )
            dryer_mass_transfer_coefficient_kg_m2_s = min(
                max(
                    (dryer_evaporation_load_kg_hr / 3600.0) / max(dryer_heat_transfer_area_m2 * moisture_driving_force, 1e-6),
                    0.0005,
                ),
                0.0800,
            )
            traces.extend(
                [
                    CalcTrace(
                        trace_id="crystallization_solubility_basis",
                        title="Crystallizer solubility-limited basis",
                        formula="m_precipitated = m_product; m_dissolved = m_recycle + m_waste; yield = m_precipitated / (m_precipitated + m_dissolved)",
                        substitutions={
                            "unit_id": crystal_packet.unit_id,
                            "component": crystal_component,
                            "model": crystal_packet.equilibrium_model or "heuristic_sle_fallback",
                            "parameter_ids": ", ".join(crystal_packet.equilibrium_parameter_ids) or "none",
                            "m_product": f"{precipitated_mass:.3f}",
                            "m_recycle_plus_waste": f"{dissolved_mass:.3f}",
                        },
                        result=f"{crystal_yield:.4f}",
                        units="-",
                        notes=(
                            "SLE basis falls back to heuristic solid/liquid splitting when cited solubility curves are unavailable."
                            if crystal_packet.equilibrium_fallback
                            else "SLE yield basis comes from the solved solubility-limited crystallization packet."
                        ),
                    ),
                    CalcTrace(
                        trace_id="crystallization_component_yield",
                        title="Crystal product yield basis",
                        formula="yield_mass = crystal product mass; dissolved loss = mother liquor + bleed",
                        substitutions={
                            "component": crystal_component,
                            "crystal_product_mass": f"{precipitated_mass:.3f}",
                            "dissolved_loss_mass": f"{dissolved_mass:.3f}",
                        },
                        result=f"{precipitated_mass:.3f}",
                        units="kg/h",
                        notes="This trace makes the solubility-limited crystal recovery explicit for the product-bearing solids train.",
                    ),
                    CalcTrace(
                        trace_id="crystallizer_supersaturation_basis",
                        title="Crystallizer supersaturation basis",
                        formula="S = feed loading / solubility limit",
                        substitutions={
                            "feed_loading": f"{crystallizer_feed_loading_kg_per_kg:.4f}",
                            "solubility_limit": f"{crystallizer_solubility_limit_kg_per_kg:.4f}" if crystallizer_solubility_limit_kg_per_kg > 0.0 else "fallback",
                            "temperature_c": f"{crystal_temperature_c:.1f}",
                        },
                        result=f"{crystallizer_supersaturation_ratio:.4f}",
                        units="-",
                        notes="This uses the resolved solubility curve when available and remains explicit when the curve falls back.",
                    ),
                    CalcTrace(
                        trace_id="filtration_area_basis",
                        title="Filtration area basis",
                        formula="Afilter = Qfiltrate / flux",
                        substitutions={
                            "filtrate_mass_kg_hr": f"{filtrate_mass:.3f}",
                            "density": f"{process_density:.3f}",
                            "flux": f"{filter_flux_m3_m2_hr:.3f}",
                        },
                        result=f"{filter_area_m2:.3f}",
                        units="m2",
                        notes="Filter area is a screening basis from the solved mother-liquor removal rate.",
                    ),
                    CalcTrace(
                        trace_id="crystallizer_holdup_basis",
                        title="Crystallizer residence-time and holdup basis",
                        formula="Vhold = Qslurry * tau",
                        substitutions={
                            "Qslurry": f"{slurry_volumetric_flow_m3_hr:.3f}",
                            "rho_slurry": f"{crystal_slurry_density_kg_m3:.3f}",
                            "tau": f"{crystallizer_residence_time_hr:.3f}",
                        },
                        result=f"{crystallizer_holdup_m3:.3f}",
                        units="m3",
                        notes="This is the preliminary crystallizer hold-up basis derived from the solved slurry rate and supersaturation severity.",
                    ),
                    CalcTrace(
                        trace_id="crystal_growth_basis",
                        title="Crystal growth screening basis",
                        formula="tau = Ltarget / Ggrowth",
                        substitutions={
                            "Ltarget": f"{target_crystal_size_mm:.3f}",
                            "Ggrowth": f"{crystal_growth_rate_mm_hr:.3f}",
                            "supersaturation": f"{crystallizer_supersaturation_ratio:.3f}",
                        },
                        result=f"{crystallizer_residence_time_hr:.3f}",
                        units="h",
                        notes="Crystal growth screening ties slurry residence time to the target crystal size and supersaturation severity.",
                    ),
                    CalcTrace(
                        trace_id="crystal_size_distribution_basis",
                        title="Crystal size distribution basis",
                        formula="PSD screening derives d10/d50/d90 around the target crystal size",
                        substitutions={
                            "d10": f"{crystal_size_d10_mm:.3f}",
                            "d50": f"{crystal_size_d50_mm:.3f}",
                            "d90": f"{crystal_size_d90_mm:.3f}",
                            "supersaturation": f"{crystallizer_supersaturation_ratio:.3f}",
                        },
                        result=f"{crystal_size_d50_mm:.3f}",
                        units="mm",
                        notes="This PSD screening keeps solids design tied to a target median crystal size instead of one undifferentiated crystal metric.",
                    ),
                    CalcTrace(
                        trace_id="crystal_classification_basis",
                        title="Crystal classification basis",
                        formula="classified product fraction = f(cut size, PSD span)",
                        substitutions={
                            "cut_size": f"{crystal_classifier_cut_size_mm:.3f}",
                            "d10": f"{crystal_size_d10_mm:.3f}",
                            "d50": f"{crystal_size_d50_mm:.3f}",
                            "d90": f"{crystal_size_d90_mm:.3f}",
                        },
                        result=f"{crystal_classified_product_fraction:.4f}",
                        units="-",
                        notes="This exposes the screening classification split between on-spec crystals and recycle fines.",
                    ),
                    CalcTrace(
                        trace_id="slurry_circulation_basis",
                        title="Slurry circulation basis",
                        formula="Qcirc = Qslurry * circulation factor",
                        substitutions={
                            "Qslurry": f"{slurry_volumetric_flow_m3_hr:.3f}",
                            "factor": f"{slurry_circulation_factor:.3f}",
                        },
                        result=f"{slurry_circulation_rate_m3_hr:.3f}",
                        units="m3/h",
                        notes="This captures the internal slurry recirculation burden used for crystallizer suspension and solids management.",
                    ),
                    CalcTrace(
                        trace_id="filter_throughput_basis",
                        title="Filter cake throughput basis",
                        formula="throughput = mcake / Afilter",
                        substitutions={
                            "mcake": f"{wet_cake_mass:.3f}",
                            "Afilter": f"{filter_area_m2:.3f}",
                        },
                        result=f"{filter_cake_throughput_kg_m2_hr:.3f}",
                        units="kg/m2-h",
                        notes="This exposes the solids-handling intensity on the selected filtration basis.",
                    ),
                    CalcTrace(
                        trace_id="filter_resistance_basis",
                        title="Filter resistance basis",
                        formula="alpha_cake = f(particle size, porosity); Rm = medium screening resistance",
                        substitutions={
                            "particle_size_m": f"{particle_size_m:.6f}",
                            "porosity": f"{crystal_porosity:.4f}",
                            "alpha_cake": f"{filter_specific_cake_resistance_m_kg:.3e}",
                            "Rm": f"{filter_medium_resistance_1_m:.3e}",
                        },
                        result=f"{filter_specific_cake_resistance_m_kg:.3e}",
                        units="m/kg",
                        notes="This adds transport-limited filter resistance screening on top of the cake throughput basis.",
                    ),
                    CalcTrace(
                        trace_id="dryer_evaporation_basis",
                        title="Dryer evaporation basis",
                        formula="m_evap = water in wet cake - water at endpoint moisture",
                        substitutions={
                            "wet_cake_moisture_fraction": f"{filter_cake_moisture_fraction:.4f}",
                            "dryer_feed_water_kg_hr": f"{_stream_component_mass_kg_hr(stream_table, drying_packet.inlet_stream_ids, 'Water') if drying_packet is not None else wet_cake_water_mass:.3f}",
                            "dryer_product_water_kg_hr": f"{design_product_water if drying_packet is not None else 0.0:.3f}",
                            "target_moisture_fraction": f"{dryer_target_moisture_fraction:.4f}",
                        },
                        result=f"{dryer_evaporation_load_kg_hr:.3f}",
                        units="kg/h",
                        notes="Dryer basis now shows the moisture removed from the solved wet-cake stream.",
                    ),
                    CalcTrace(
                        trace_id="dryer_refined_duty_basis",
                        title="Dryer refined duty basis",
                        formula="Qdryer = m_evap*lambda + m_dry*Cp*DeltaT",
                        substitutions={
                            "m_evap": f"{dryer_evaporation_load_kg_hr:.3f}",
                            "m_dry": f"{dry_crystal_mass:.3f}",
                            "tau": f"{dryer_residence_time_hr:.3f}",
                        },
                        result=f"{dryer_refined_duty_kw:.3f}",
                        units="kW",
                        notes="This refines the dryer basis with latent moisture removal plus sensible heating of the dry crystal bed.",
                    ),
                    CalcTrace(
                        trace_id="dryer_moisture_endpoint_basis",
                        title="Dryer moisture-endpoint basis",
                        formula="xH2O,prod = mwater,prod / (mwater,prod + mdry)",
                        substitutions={
                            "mwater,prod": f"{design_product_water:.3f}",
                            "mdry": f"{dry_crystal_mass:.3f}",
                            "target_moisture_fraction": f"{dryer_target_moisture_fraction:.4f}",
                        },
                        result=f"{dryer_product_moisture_fraction:.4f}",
                        units="-",
                        notes="Endpoint moisture is now explicit so the dryer design basis does not stop at evaporation load alone.",
                    ),
                    CalcTrace(
                        trace_id="dryer_exhaust_humidity_basis",
                        title="Dryer exhaust humidity basis",
                        formula="Yout = Yin + mevap/m_dry_air ; saturation fraction = Yout/Ysat",
                        substitutions={
                            "Yin": f"{dryer_inlet_humidity_ratio_kg_kg:.4f}",
                            "mdry_air": f"{dryer_dry_air_flow_kg_hr:.3f}",
                            "Yout": f"{dryer_exhaust_humidity_ratio_kg_kg:.4f}",
                            "sat_fraction": f"{dryer_exhaust_saturation_fraction:.4f}",
                        },
                        result=f"{dryer_exhaust_humidity_ratio_kg_kg:.4f}",
                        units="kg/kg dry air",
                        notes="This adds an exhaust-side humidity constraint so dryer endpoint logic reflects air-side carrying capacity.",
                    ),
                    CalcTrace(
                        trace_id="dryer_heat_mass_transfer_basis",
                        title="Dryer heat and mass-transfer basis",
                        formula="Q = U*A*dT ; Nw = kY*A*driving force",
                        substitutions={
                            "U": f"{dryer_heat_transfer_coefficient_w_m2_k:.3f}",
                            "A": f"{dryer_heat_transfer_area_m2:.3f}",
                            "kY": f"{dryer_mass_transfer_coefficient_kg_m2_s:.5f}",
                            "xeq": f"{dryer_equilibrium_moisture_fraction:.4f}",
                        },
                        result=f"{dryer_refined_duty_kw:.3f}",
                        units="kW",
                        notes="This extends the dryer endpoint basis into explicit heat-transfer and mass-transfer screening terms.",
                    ),
                ]
            )
    return ColumnDesign(
        column_id="PU-201",
        service=service,
        light_key=light_key,
        heavy_key=heavy_key,
        relative_volatility=round(alpha, 3),
        min_stages=round(min_stages, 3),
        theoretical_stages=round(theoretical_stages, 3),
        design_stages=stages,
        tray_efficiency=round(tray_efficiency, 3),
        minimum_reflux_ratio=round(min_reflux, 3),
        reflux_ratio=round(reflux, 3),
        reflux_ratio_multiple_of_min=round(reflux / max(min_reflux, 1e-6), 3),
        column_diameter_m=round(diameter, 3),
        column_height_m=round(height, 3),
        condenser_duty_kw=round(condenser, 3),
        reboiler_duty_kw=round(reboiler, 3),
        vapor_load_kg_hr=round(reboiler_phase_change_load, 3),
        liquid_load_m3_hr=round(liquid_load_m3_hr, 3),
        vapor_density_kg_m3=round(vapor_density, 3),
        liquid_density_kg_m3=round(process_density, 3),
        feed_stage=feed_stage,
        tray_spacing_m=tray_spacing,
        flooding_fraction=round(flooding_fraction, 3),
        downcomer_area_fraction=round(downcomer_fraction, 3),
        allowable_vapor_velocity_m_s=round(allowable_vapor_velocity, 3),
        superficial_vapor_velocity_m_s=round(superficial_vapor_velocity, 3),
        pressure_drop_per_stage_kpa=round(pressure_drop_per_stage, 3),
        top_temperature_c=round(top_temp, 1),
        bottom_temperature_c=round(bottom_temp, 1),
        utility_topology=utility_architecture.architecture.topology_summary if utility_architecture else "",
        integrated_reboiler_duty_kw=round(integrated_reboiler, 3),
        residual_reboiler_utility_kw=round(max(reboiler - integrated_reboiler, 0.0), 3),
        integrated_reboiler_lmtd_k=round(reboiler_lmtd, 3),
        integrated_reboiler_area_m2=round(reboiler_area, 3),
        reboiler_medium=_step_media_summary(heating_train_steps),
        reboiler_package_type=reboiler_package.equipment_type if reboiler_package is not None else "",
        reboiler_circulation_ratio=round(reboiler_package.circulation_ratio if reboiler_package is not None else 3.0, 3),
        reboiler_phase_change_load_kg_hr=round(reboiler_phase_change_load, 3),
        reboiler_package_item_ids=[item.package_item_id for step in heating_train_steps for item in step.package_items if item.package_family == "reboiler"],
        condenser_recovery_duty_kw=round(condenser_recovery, 3),
        condenser_recovery_lmtd_k=round(condenser_lmtd, 3),
        condenser_recovery_area_m2=round(condenser_area, 3),
        condenser_recovery_medium=_step_media_summary(condenser_train_steps),
        condenser_package_type=condenser_package.equipment_type if condenser_package is not None else "",
        condenser_phase_change_load_kg_hr=round(condenser_phase_change_load, 3),
        condenser_circulation_flow_m3_hr=round(condenser_package.flow_m3_hr if condenser_package is not None else liquid_load_m3_hr, 3),
        condenser_package_item_ids=[item.package_item_id for step in condenser_train_steps for item in step.package_items if item.package_family == "condenser"],
        equilibrium_model=", ".join(equilibrium_models) or "",
        equilibrium_parameter_ids=equilibrium_parameter_ids,
        equilibrium_fallback=equilibrium_fallback,
        absorber_key_component=absorber_key_component,
        absorber_henry_constant_bar=round(absorber_henry_constant_bar, 6),
        absorber_equilibrium_slope=round(absorber_equilibrium_slope, 6),
        absorber_solvent_to_gas_ratio=round(absorber_solvent_to_gas_ratio, 6),
        absorber_capture_fraction=round(absorber_capture_fraction, 6),
        absorber_stage_efficiency=round(absorber_stage_efficiency, 6),
        absorber_theoretical_stages=round(absorber_theoretical_stages, 6),
        absorber_packed_height_m=round(absorber_packed_height_m, 6),
        absorber_gas_mass_velocity_kg_m2_s=round(absorber_gas_mass_velocity_kg_m2_s, 6),
        absorber_liquid_mass_velocity_kg_m2_s=round(absorber_liquid_mass_velocity_kg_m2_s, 6),
        absorber_ntu=round(absorber_ntu, 6),
        absorber_htu_m=round(absorber_htu_m, 6),
        absorber_overall_mass_transfer_coefficient_1_s=round(absorber_overall_mass_transfer_coefficient_1_s, 6),
        absorber_packing_family=absorber_packing_family,
        absorber_packing_specific_area_m2_m3=round(absorber_packing_specific_area_m2_m3, 6),
        absorber_effective_interfacial_area_m2_m3=round(absorber_effective_interfacial_area_m2_m3, 6),
        absorber_gas_phase_transfer_coeff_1_s=round(absorber_gas_phase_transfer_coeff_1_s, 6),
        absorber_liquid_phase_transfer_coeff_1_s=round(absorber_liquid_phase_transfer_coeff_1_s, 6),
        absorber_min_wetting_rate_kg_m2_s=round(absorber_min_wetting_rate_kg_m2_s, 6),
        absorber_wetting_ratio=round(absorber_wetting_ratio, 6),
        absorber_operating_velocity_m_s=round(absorber_operating_velocity_m_s, 6),
        absorber_flooding_velocity_m_s=round(absorber_flooding_velocity_m_s, 6),
        absorber_flooding_margin_fraction=round(absorber_flooding_margin_fraction, 6),
        absorber_pressure_drop_per_m_kpa_m=round(absorber_pressure_drop_per_m_kpa_m, 6),
        absorber_total_pressure_drop_kpa=round(absorber_total_pressure_drop_kpa, 6),
        crystallizer_key_component=crystallizer_key_component,
        crystallizer_solubility_limit_kg_per_kg=round(crystallizer_solubility_limit_kg_per_kg, 6),
        crystallizer_feed_loading_kg_per_kg=round(crystallizer_feed_loading_kg_per_kg, 6),
        crystallizer_supersaturation_ratio=round(crystallizer_supersaturation_ratio, 6),
        crystallizer_precipitated_mass_kg_hr=round(crystallizer_precipitated_mass_kg_hr, 6),
        crystallizer_dissolved_mass_kg_hr=round(crystallizer_dissolved_mass_kg_hr, 6),
        crystallizer_yield_fraction=round(crystallizer_yield_fraction, 6),
        crystallizer_residence_time_hr=round(crystallizer_residence_time_hr, 6),
        crystallizer_holdup_m3=round(crystallizer_holdup_m3, 6),
        crystal_slurry_density_kg_m3=round(crystal_slurry_density_kg_m3, 6),
        crystal_growth_rate_mm_hr=round(crystal_growth_rate_mm_hr, 6),
        crystal_size_d10_mm=round(crystal_size_d10_mm, 6),
        crystal_size_d50_mm=round(crystal_size_d50_mm, 6),
        crystal_size_d90_mm=round(crystal_size_d90_mm, 6),
        crystal_classifier_cut_size_mm=round(crystal_classifier_cut_size_mm, 6),
        crystal_classified_product_fraction=round(crystal_classified_product_fraction, 6),
        slurry_circulation_rate_m3_hr=round(slurry_circulation_rate_m3_hr, 6),
        filter_cake_moisture_fraction=round(filter_cake_moisture_fraction, 6),
        filter_area_m2=round(filter_area_m2, 6),
        filter_cake_throughput_kg_m2_hr=round(filter_cake_throughput_kg_m2_hr, 6),
        filter_specific_cake_resistance_m_kg=round(filter_specific_cake_resistance_m_kg, 6),
        filter_medium_resistance_1_m=round(filter_medium_resistance_1_m, 6),
        dryer_evaporation_load_kg_hr=round(dryer_evaporation_load_kg_hr, 6),
        dryer_residence_time_hr=round(dryer_residence_time_hr, 6),
        dryer_target_moisture_fraction=round(dryer_target_moisture_fraction, 6),
        dryer_product_moisture_fraction=round(dryer_product_moisture_fraction, 6),
        dryer_equilibrium_moisture_fraction=round(dryer_equilibrium_moisture_fraction, 6),
        dryer_inlet_humidity_ratio_kg_kg=round(dryer_inlet_humidity_ratio_kg_kg, 6),
        dryer_exhaust_humidity_ratio_kg_kg=round(dryer_exhaust_humidity_ratio_kg_kg, 6),
        dryer_dry_air_flow_kg_hr=round(dryer_dry_air_flow_kg_hr, 6),
        dryer_exhaust_saturation_fraction=round(dryer_exhaust_saturation_fraction, 6),
        dryer_mass_transfer_coefficient_kg_m2_s=round(dryer_mass_transfer_coefficient_kg_m2_s, 6),
        dryer_heat_transfer_coefficient_w_m2_k=round(dryer_heat_transfer_coefficient_w_m2_k, 6),
        dryer_heat_transfer_area_m2=round(dryer_heat_transfer_area_m2, 6),
        dryer_refined_duty_kw=round(dryer_refined_duty_kw, 6),
        selected_train_step_ids=[step.step_id for step in heating_train_steps + condenser_train_steps],
        calc_traces=traces,
        value_records=[
            make_value_record("process_unit_relative_volatility", "Process-unit relative volatility", alpha, "-", citations=route.citations, assumptions=route.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("process_unit_stages", "Process-unit design stages", stages, "stages", citations=route.citations, assumptions=route.assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("process_unit_reboiler_duty", "Process-unit heating duty", reboiler, "kW", citations=energy_balance.citations, assumptions=energy_balance.assumptions, sensitivity=SensitivityLevel.HIGH),
            *(
                [
                    make_value_record(
                        "absorber_capture_fraction",
                        "Absorber capture fraction",
                        absorber_capture_fraction,
                        "-",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.HIGH,
                    ),
                    make_value_record(
                        "absorber_packed_height",
                        "Absorber packed height",
                        absorber_packed_height_m,
                        "m",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                    make_value_record(
                        "absorber_total_pressure_drop",
                        "Absorber total pressure drop",
                        absorber_total_pressure_drop_kpa,
                        "kPa",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                    make_value_record(
                        "absorber_wetting_ratio",
                        "Absorber wetting ratio",
                        absorber_wetting_ratio,
                        "-",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                    make_value_record(
                        "absorber_flooding_margin",
                        "Absorber flooding margin",
                        absorber_flooding_margin_fraction,
                        "-",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                ]
                if absorber_key_component
                else []
            ),
            *(
                [
                    make_value_record(
                        "crystallizer_yield_fraction",
                        "Crystallizer yield fraction",
                        crystallizer_yield_fraction,
                        "-",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.HIGH,
                    ),
                    make_value_record(
                        "filter_area",
                        "Filter area",
                        filter_area_m2,
                        "m2",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                    make_value_record(
                        "dryer_product_moisture_fraction",
                        "Dryer product moisture fraction",
                        dryer_product_moisture_fraction,
                        "-",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                    make_value_record(
                        "crystal_size_d50",
                        "Crystal median size",
                        crystal_size_d50_mm,
                        "mm",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                    make_value_record(
                        "dryer_exhaust_humidity_ratio",
                        "Dryer exhaust humidity ratio",
                        dryer_exhaust_humidity_ratio_kg_kg,
                        "kg/kg dry air",
                        citations=(property_packages.citations if property_packages is not None else route.citations),
                        assumptions=(property_packages.assumptions if property_packages is not None else route.assumptions),
                        sensitivity=SensitivityLevel.MEDIUM,
                    ),
                ]
                if crystallizer_key_component
                else []
            ),
        ],
        citations=sorted(set(route.citations + energy_balance.citations + (separation_choice.citations if separation_choice else []) + (property_packages.citations if property_packages is not None else []))),
        assumptions=route.assumptions + energy_balance.assumptions + (separation_choice.assumptions if separation_choice else []) + (property_packages.assumptions if property_packages is not None else []),
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
    if package_family == "reboiler":
        boiling_coeff = 2400.0 if exchanger_package is not None and "kettle" in exchanger_type else 1850.0
        condensing_coeff = 850.0
    elif package_family == "condenser":
        boiling_coeff = 900.0
        condensing_coeff = 2600.0 if exchanger_package is not None and selected_step is not None and selected_step.medium.lower() == "direct" else 2100.0
    else:
        boiling_coeff = 1200.0
        condensing_coeff = 1200.0
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
        boiling_side_coefficient_w_m2_k=round(boiling_coeff, 3),
        condensing_side_coefficient_w_m2_k=round(condensing_coeff, 3),
        utility_topology=utility_architecture.architecture.topology_summary if utility_architecture is not None else "",
        selected_train_step_id=selected_step.step_id if selected_step is not None else None,
        selected_package_item_ids=[item.package_item_id for item in selected_package_items],
        selected_package_roles=sorted({item.package_role for item in selected_package_items}),
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
    if "absorption" in column.service.lower() and column.absorber_packing_family:
        packed_cross_section_m2 = math.pi * (column.column_diameter_m / 2.0) ** 2 * max(1.0 - column.downcomer_area_fraction, 0.25)
        packed_volume_m3 = max(packed_cross_section_m2 * max(column.absorber_packed_height_m, 2.0), 1.0)
        absorber_transport_kw = max(
            column.absorber_total_pressure_drop_kpa * packed_cross_section_m2 * max(column.absorber_operating_velocity_m_s, 0.1) / 0.62,
            2.0,
        )
        equipment.append(
            EquipmentSpec(
                equipment_id=f"{column.column_id}_packing",
                equipment_type="Packing internals",
                service=f"{column.absorber_packing_family} packing",
                design_basis=(
                    f"{column.absorber_packing_specific_area_m2_m3:.0f} m2/m3 packing with "
                    f"{column.absorber_effective_interfacial_area_m2_m3:.0f} m2/m3 effective area"
                ),
                volume_m3=round(packed_volume_m3, 3),
                design_temperature_c=column.bottom_temperature_c or 120.0,
                design_pressure_bar=max(column.design_stages * 0.05 + 1.5, 2.0),
                material_of_construction=moc,
                duty_kw=round(absorber_transport_kw, 3),
                notes="Packed-absorber internals sized from transport-limited wetting, flooding, and transfer-unit screening.",
                citations=column.citations,
                assumptions=column.assumptions,
            )
        )
    if "crystallizer" in column.service.lower() and column.crystallizer_key_component:
        equipment.extend(
            [
                EquipmentSpec(
                    equipment_id=f"{column.column_id}_classifier",
                    equipment_type="Crystal classifier",
                    service="Crystal cut-size control",
                    design_basis=f"Cut size {column.crystal_classifier_cut_size_mm:.3f} mm at classified fraction {column.crystal_classified_product_fraction:.3f}",
                    volume_m3=round(max(column.slurry_circulation_rate_m3_hr * 0.05, 1.0), 3),
                    design_temperature_c=max(column.bottom_temperature_c, 35.0),
                    design_pressure_bar=1.5,
                    material_of_construction=moc,
                    duty_kw=round(max(column.slurry_circulation_rate_m3_hr * 0.12, 4.0), 3),
                    notes="Classifier sizing follows the solved crystal-size distribution and fines cut.",
                    citations=column.citations,
                    assumptions=column.assumptions,
                ),
                EquipmentSpec(
                    equipment_id=f"{column.column_id}_filter",
                    equipment_type="Pressure filter",
                    service="Cake filtration",
                    design_basis=f"Filter area {column.filter_area_m2:.3f} m2 with cake resistance {column.filter_specific_cake_resistance_m_kg:.3e} m/kg",
                    volume_m3=round(max(column.filter_area_m2 * 0.06, 1.2), 3),
                    design_temperature_c=max(column.top_temperature_c, 30.0),
                    design_pressure_bar=2.0,
                    material_of_construction=moc,
                    duty_kw=round(max(column.filter_specific_cake_resistance_m_kg / 1.5e9, 3.0), 3),
                    notes="Filter package sizing follows the solids throughput and transport-limited resistance basis.",
                    citations=column.citations,
                    assumptions=column.assumptions,
                ),
                EquipmentSpec(
                    equipment_id=f"{column.column_id}_dryer_air",
                    equipment_type="Dryer gas handling skid",
                    service="Dryer circulation and exhaust handling",
                    design_basis=f"Dry-air flow {column.dryer_dry_air_flow_kg_hr:.3f} kg/h with exhaust humidity {column.dryer_exhaust_humidity_ratio_kg_kg:.4f} kg/kg",
                    volume_m3=round(max(column.dryer_heat_transfer_area_m2 * 0.04, 1.0), 3),
                    design_temperature_c=max(column.bottom_temperature_c, 85.0),
                    design_pressure_bar=1.4,
                    material_of_construction=moc,
                    duty_kw=round(max(column.dryer_dry_air_flow_kg_hr / 9000.0, 4.0), 3),
                    notes="Dryer gas package sizing follows the endpoint humidity and air-side transfer basis.",
                    citations=column.citations,
                    assumptions=column.assumptions,
                ),
            ]
        )
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
