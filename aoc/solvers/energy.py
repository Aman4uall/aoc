from __future__ import annotations

from aoc.models import (
    CalcTrace,
    EnergyBalance,
    ExchangerNetworkCandidate,
    RouteOption,
    SensitivityLevel,
    StreamTable,
    ThermoAssessmentArtifact,
    UnitDuty,
    UnitThermalPacket,
)
from aoc.value_engine import make_value_record


def _sensible_duty_kw(mass_flow_kg_hr: float, cp_kj_kg_k: float, delta_t_k: float) -> float:
    return (mass_flow_kg_hr * cp_kj_kg_k * max(delta_t_k, 0.0)) / 3600.0


def _latent_duty_kw(mass_flow_kg_hr: float, latent_heat_kj_kg: float) -> float:
    return (mass_flow_kg_hr * latent_heat_kj_kg) / 3600.0


def _separation_family(route: RouteOption) -> str:
    text = " ".join(route.separations).lower()
    if "absor" in text or "strip" in text:
        return "absorption"
    if "crystal" in text or "filter" in text or "dry" in text:
        return "solids"
    if "extract" in text:
        return "extraction"
    if "distill" in text or "vacuum" in text or "flash" in text:
        return "distillation"
    return "generic"


def _stream_mass(stream_table: StreamTable, stream_id: str) -> float:
    for stream in stream_table.streams:
        if stream.stream_id == stream_id:
            return sum(component.mass_flow_kg_hr for component in stream.components)
    return 0.0


def _stream_kmol(stream_table: StreamTable, stream_id: str) -> float:
    for stream in stream_table.streams:
        if stream.stream_id == stream_id:
            return sum(component.molar_flow_kmol_hr for component in stream.components)
    return 0.0


def _product_stream(stream_table: StreamTable):
    for stream in stream_table.streams:
        if "on-spec product" in stream.description.lower():
            return stream
    for stream in stream_table.streams:
        if stream.stream_id == "S-401":
            return stream
    return stream_table.streams[-1]


def _stream_record(stream_table: StreamTable, stream_id: str | None):
    if not stream_id:
        return None
    return next((stream for stream in stream_table.streams if stream.stream_id == stream_id), None)


def _temperature_for_stream(stream_table: StreamTable, stream_id: str | None, default: float) -> float:
    stream = _stream_record(stream_table, stream_id)
    return stream.temperature_c if stream is not None else default


def _packet_media(duty: UnitDuty) -> list[str]:
    lowered = f"{duty.unit_id} {duty.notes} {duty.duty_type}".lower()
    media: list[str] = []
    if duty.cooling_kw > 0.0:
        if "reactor" in lowered or duty.unit_id.startswith("R-") or duty.unit_id.startswith("CONV"):
            media.extend(["Dowtherm A", "cooling water"])
        elif "condenser" in lowered or duty.unit_id.startswith("D-") or duty.unit_id.startswith("V-"):
            media.extend(["direct", "cooling water"])
        else:
            media.extend(["cooling water"])
    if duty.heating_kw > 0.0:
        if "reboiler" in lowered or duty.unit_id.startswith("D-") or duty.unit_id.startswith("EV-"):
            media.extend(["Dowtherm A", "steam"])
        elif duty.unit_id.startswith("DRY"):
            media.extend(["steam", "hot air"])
        else:
            media.extend(["steam", "hot oil"])
    return list(dict.fromkeys(media))


def _build_thermal_packets(
    route: RouteOption,
    stream_table: StreamTable,
    duties: list[UnitDuty],
) -> list[UnitThermalPacket]:
    packets: list[UnitThermalPacket] = []
    for duty in duties:
        hot_supply = _temperature_for_stream(
            stream_table,
            duty.hot_stream_id,
            route.operating_temperature_c + (30.0 if duty.heating_kw > 0.0 else 20.0 if duty.duty_type == "reaction" else 5.0),
        )
        cold_supply = _temperature_for_stream(stream_table, duty.cold_stream_id, 30.0) if duty.heating_kw > 0.0 else 30.0
        if duty.cooling_kw > 0.0:
            hot_target_candidate = _temperature_for_stream(
                stream_table,
                duty.cold_stream_id,
                hot_supply - (45.0 if duty.duty_type == "reaction" else 25.0),
            )
            hot_target = min(hot_target_candidate, hot_supply - 5.0)
            if hot_target >= hot_supply:
                hot_target = max(hot_supply - 10.0, 25.0)
        else:
            hot_target = max(hot_supply - 15.0, cold_supply + 5.0)
        if duty.heating_kw > 0.0:
            cold_target = max(
                cold_supply + 5.0,
                min(
                    route.operating_temperature_c if duty.unit_id.startswith("E-101") or duty.unit_id.startswith("R-") else cold_supply + (70.0 if duty.duty_type in {"latent", "reaction"} else 45.0),
                    max(hot_supply - 8.0, cold_supply + 10.0),
                ),
            )
        else:
            cold_target = min(max(cold_supply + 12.0, 42.0), max(hot_target - 3.0, cold_supply + 8.0))
        recoverable = min(duty.heating_kw, duty.cooling_kw) if duty.heating_kw > 0.0 and duty.cooling_kw > 0.0 else 0.0
        packets.append(
            UnitThermalPacket(
                packet_id=f"{duty.unit_id}_thermal_packet",
                unit_id=duty.unit_id,
                service=duty.notes or duty.unit_id,
                duty_type=duty.duty_type,
                heating_kw=round(duty.heating_kw, 3),
                cooling_kw=round(duty.cooling_kw, 3),
                hot_stream_id=duty.hot_stream_id,
                cold_stream_id=duty.cold_stream_id,
                hot_supply_temp_c=round(hot_supply, 3),
                hot_target_temp_c=round(hot_target, 3),
                cold_supply_temp_c=round(cold_supply, 3),
                cold_target_temp_c=round(cold_target, 3),
                recoverable_duty_kw=round(recoverable, 3),
                candidate_media=_packet_media(duty),
                notes=[duty.notes] if duty.notes else [],
                citations=stream_table.citations,
                assumptions=stream_table.assumptions,
            )
        )
    return packets


def _build_network_candidates(packets: list[UnitThermalPacket], min_approach_temp_c: float = 20.0) -> list[ExchangerNetworkCandidate]:
    hot_packets = [packet for packet in packets if packet.cooling_kw > 0.0]
    cold_packets = [packet for packet in packets if packet.heating_kw > 0.0]
    candidates: list[ExchangerNetworkCandidate] = []
    for hot_packet in hot_packets:
        for cold_packet in cold_packets:
            if hot_packet.unit_id == cold_packet.unit_id:
                continue
            direct_margin = hot_packet.hot_supply_temp_c - cold_packet.cold_target_temp_c
            indirect_margin = hot_packet.hot_supply_temp_c - cold_packet.cold_supply_temp_c
            topology = "direct" if direct_margin >= min_approach_temp_c else "htm_loop"
            feasible = direct_margin >= min_approach_temp_c or indirect_margin >= min_approach_temp_c
            recovered = min(hot_packet.cooling_kw, cold_packet.heating_kw)
            if not feasible or recovered <= 0.0:
                continue
            if topology == "direct":
                recovered *= 0.90
            else:
                recovered *= 0.76
            candidates.append(
                ExchangerNetworkCandidate(
                    candidate_id=f"{hot_packet.unit_id}_to_{cold_packet.unit_id}",
                    source_unit_id=hot_packet.unit_id,
                    sink_unit_id=cold_packet.unit_id,
                    hot_packet_id=hot_packet.packet_id,
                    cold_packet_id=cold_packet.packet_id,
                    topology=topology,
                    recovered_duty_kw=round(recovered, 3),
                    minimum_approach_temp_c=min_approach_temp_c,
                    feasible=True,
                    notes=(
                        "Direct packet-level recovery candidate."
                        if topology == "direct"
                        else "Indirect hot-transfer-medium candidate derived from solved unit duties."
                    ),
                    citations=sorted(set(hot_packet.citations + cold_packet.citations)),
                    assumptions=sorted(set(hot_packet.assumptions + cold_packet.assumptions)),
                )
            )
    candidates.sort(key=lambda item: item.recovered_duty_kw, reverse=True)
    return candidates


def build_energy_balance_generic(route: RouteOption, stream_table: StreamTable, thermo: ThermoAssessmentArtifact) -> EnergyBalance:
    feed_mass = 0.0
    recycle_mass = 0.0
    for stream in stream_table.streams:
        total_mass = sum(component.mass_flow_kg_hr for component in stream.components)
        if stream.stream_id.startswith("S-10"):
            feed_mass += total_mass
        if stream.stream_id == "S-301":
            recycle_mass = total_mass
    product_stream = _product_stream(stream_table)
    product_mass = sum(component.mass_flow_kg_hr for component in product_stream.components)
    product_kmol_hr = sum(component.molar_flow_kmol_hr for component in product_stream.components)
    family = _separation_family(route)
    mixed_feed_mass = _stream_mass(stream_table, "S-150") or feed_mass
    flash_bottom_mass = _stream_mass(stream_table, "S-203")
    concentration_overhead_mass = _stream_mass(stream_table, "S-301")
    concentration_bottom_mass = _stream_mass(stream_table, "S-302")
    light_ends_mass = _stream_mass(stream_table, "S-401") if product_stream.stream_id != "S-401" else _stream_mass(stream_table, "S-403")
    preheat_kw = _sensible_duty_kw(mixed_feed_mass, 2.9 if family != "solids" else 1.8, route.operating_temperature_c - 25.0)
    reaction_kw = abs(product_kmol_hr * 1000.0 * thermo.estimated_reaction_enthalpy_kj_per_mol / 3600.0)
    exothermic = thermo.estimated_reaction_enthalpy_kj_per_mol < 0
    duties = [
        UnitDuty(unit_id="E-101", heating_kw=round(preheat_kw, 3), cooling_kw=0.0, notes="Feed preheat to operating temperature.", duty_type="sensible", cold_stream_id="S-150"),
        UnitDuty(
            unit_id="R-101",
            heating_kw=0.0 if exothermic else round(reaction_kw, 3),
            cooling_kw=round(reaction_kw, 3) if exothermic else 0.0,
            notes="Net reactor thermal duty from the selected thermodynamic basis.",
            duty_type="reaction",
            hot_stream_id="S-201" if exothermic else None,
            cold_stream_id="S-150" if not exothermic else None,
        ),
    ]
    if family == "distillation":
        flash_cooler_kw = _sensible_duty_kw(_stream_mass(stream_table, "S-201"), 3.1, max(route.operating_temperature_c - 95.0, 0.0))
        preconcentrator_kw = _latent_duty_kw(max(concentration_overhead_mass, flash_bottom_mass * 0.35), 2200.0)
        precondenser_kw = preconcentrator_kw * 0.93
        reboiler_kw = _latent_duty_kw(max(concentration_bottom_mass * 0.28, product_mass * 0.18), 2150.0)
        condenser_kw = reboiler_kw * 0.88
        product_cooler_kw = _sensible_duty_kw(product_mass, 2.7, 75.0)
        duties.extend(
            [
                UnitDuty(unit_id="V-101", heating_kw=0.0, cooling_kw=round(flash_cooler_kw, 3), notes="Reactor effluent trim cooling before primary flash.", duty_type="sensible", hot_stream_id="S-201", cold_stream_id="S-203"),
                UnitDuty(unit_id="EV-101", heating_kw=round(preconcentrator_kw, 3), cooling_kw=round(precondenser_kw, 3), notes="Water-removal concentration duty prior to final purification.", duty_type="latent", hot_stream_id="S-301", cold_stream_id="S-302"),
                UnitDuty(unit_id="D-101", heating_kw=round(reboiler_kw, 3), cooling_kw=round(condenser_kw, 3), notes="Primary purification column duty.", duty_type="latent", hot_stream_id="S-401", cold_stream_id="S-402"),
                UnitDuty(unit_id="E-201", heating_kw=0.0, cooling_kw=round(product_cooler_kw, 3), notes="Product cooler before storage.", duty_type="sensible", hot_stream_id=product_stream.stream_id),
            ]
        )
    elif family == "absorption":
        converter_cooling = reaction_kw * 0.45 if exothermic else reaction_kw * 0.20
        absorption_cooling = max(product_mass * 0.08, 2500.0)
        regeneration_heating = max(_stream_mass(stream_table, "S-203") * 0.06, 900.0)
        duties.append(UnitDuty(unit_id="ABS-201", heating_kw=0.0, cooling_kw=round(absorption_cooling, 3), notes="Absorption and drying heat-removal duty.", duty_type="sensible", hot_stream_id="S-203"))
        duties.append(UnitDuty(unit_id="STR-201", heating_kw=round(regeneration_heating, 3), cooling_kw=round(regeneration_heating * 0.35, 3), notes="Absorbent regeneration and stripping duty.", duty_type="latent"))
        duties.append(UnitDuty(unit_id="CONV-101", heating_kw=0.0, cooling_kw=round(converter_cooling, 3), notes="Converter cooling or heat recovery duty.", duty_type="reaction"))
    elif family == "solids":
        crystallizer_kw = max(_sensible_duty_kw(product_mass, 2.1, 35.0), 1500.0)
        dryer_kw = max(_latent_duty_kw(product_mass * 0.04, 2300.0), 900.0)
        filter_aux_kw = max(product_mass * 0.015, 120.0)
        duties.append(UnitDuty(unit_id="CRYS-201", heating_kw=0.0, cooling_kw=round(crystallizer_kw, 3), notes="Crystallizer cooling duty.", duty_type="sensible", hot_stream_id="S-203"))
        duties.append(UnitDuty(unit_id="FILT-201", heating_kw=0.0, cooling_kw=round(filter_aux_kw, 3), notes="Filter wash and slurry handling auxiliary duty.", duty_type="sensible"))
        duties.append(UnitDuty(unit_id="DRY-301", heating_kw=round(dryer_kw, 3), cooling_kw=0.0, notes="Dryer heating duty.", duty_type="latent", cold_stream_id=product_stream.stream_id))
    elif family == "extraction":
        extractor_kw = max(product_mass * 0.04, 250.0)
        solvent_recovery_kw = max(product_mass * 0.12, 500.0)
        phase_split_kw = max(light_ends_mass * 0.05, 160.0)
        duties.append(UnitDuty(unit_id="EXT-201", heating_kw=round(extractor_kw, 3), cooling_kw=round(extractor_kw * 0.25, 3), notes="Extraction conditioning duty.", duty_type="sensible"))
        duties.append(UnitDuty(unit_id="DEC-201", heating_kw=0.0, cooling_kw=round(phase_split_kw, 3), notes="Phase disengagement and solvent conditioning duty.", duty_type="sensible"))
        duties.append(UnitDuty(unit_id="SR-301", heating_kw=round(solvent_recovery_kw, 3), cooling_kw=round(solvent_recovery_kw * 0.60, 3), notes="Solvent recovery duty.", duty_type="latent"))
    else:
        polish_kw = max(product_mass * 0.05, 150.0)
        duties.append(UnitDuty(unit_id="SEP-201", heating_kw=round(polish_kw, 3), cooling_kw=round(polish_kw * 0.5, 3), notes="Generic purification duty.", duty_type="sensible"))
    total_heating = round(sum(item.heating_kw for item in duties), 3)
    total_cooling = round(sum(item.cooling_kw for item in duties), 3)
    thermal_packets = _build_thermal_packets(route, stream_table, duties)
    network_candidates = _build_network_candidates(thermal_packets)
    traces = [
        CalcTrace(
            trace_id="energy_preheat",
            title="Feed preheat duty",
            formula="Q = m * Cp * dT / 3600",
            substitutions={"m": f"{feed_mass:.3f} kg/h", "dT": f"{max(route.operating_temperature_c - 25.0, 0.0):.1f} K"},
            result=f"{preheat_kw:.3f}",
            units="kW",
        ),
        CalcTrace(
            trace_id="energy_reaction",
            title="Reaction duty",
            formula="Q = |n * dH| / 3600",
            substitutions={"n": f"{product_kmol_hr:.6f} kmol/h", "dH": f"{thermo.estimated_reaction_enthalpy_kj_per_mol:.3f} kJ/mol"},
            result=f"{reaction_kw:.3f}",
            units="kW",
        ),
        CalcTrace(
            trace_id="energy_unit_count",
            title="Unitwise duty expansion",
            formula="duty_count = number of explicit unit duties in the solved energy envelope",
            result=f"{len(duties)}",
            units="duties",
            notes="The generic energy solver now emits duty rows for each major process section rather than a single family-level total.",
        ),
        CalcTrace(
            trace_id="energy_thermal_packets",
            title="Thermal packet expansion",
            formula="packet_count = number of unitwise thermal packets carried into utility and equipment design",
            result=f"{len(thermal_packets)}",
            units="packets",
            notes="These packets preserve unit-level hot and cold thermal interfaces downstream.",
        ),
        CalcTrace(
            trace_id="energy_network_candidates",
            title="Packet-derived exchanger candidates",
            formula="candidate_count = number of packet-to-packet heat-recovery candidates",
            result=f"{len(network_candidates)}",
            units="candidates",
            notes="These candidates seed utility-architecture selection and detailed exchanger sizing.",
        ),
    ]
    return EnergyBalance(
        duties=duties,
        total_heating_kw=total_heating,
        total_cooling_kw=total_cooling,
        unit_thermal_packets=thermal_packets,
        network_candidates=network_candidates,
        calc_traces=traces,
        value_records=[
            make_value_record("energy_total_heating", "Total heating duty", total_heating, "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("energy_total_cooling", "Total cooling duty", total_cooling, "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
            make_value_record("energy_reaction_duty", "Reaction duty", reaction_kw, "kW", citations=thermo.citations, assumptions=thermo.assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=thermo.citations,
        assumptions=thermo.assumptions + [f"Generic energy solver inferred `{family}` separation duty from route metadata."],
    )
