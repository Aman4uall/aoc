from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from aoc.models import CompositionClosure, StreamRecord, UnitCompositionState, UnitOperationPacket


def _aggregate_molar(streams: Iterable[StreamRecord]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for stream in streams:
        for component in stream.components:
            totals[component.name] += component.molar_flow_kmol_hr
    return {name: round(value, 6) for name, value in totals.items() if value > 1e-9}


def _aggregate_mass(streams: Iterable[StreamRecord]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for stream in streams:
        for component in stream.components:
            totals[component.name] += component.mass_flow_kg_hr
    return {name: round(value, 6) for name, value in totals.items() if value > 1e-9}


def _normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 1e-12:
        return {}
    return {name: round(value / total, 6) for name, value in values.items() if value > 1e-12}


def _dominant_phase(streams: Iterable[StreamRecord]) -> str:
    phase_mass: dict[str, float] = defaultdict(float)
    for stream in streams:
        phase_mass[stream.phase_hint or "mixed"] += sum(component.mass_flow_kg_hr for component in stream.components)
    if not phase_mass:
        return ""
    return max(phase_mass.items(), key=lambda item: item[1])[0]


def _is_reactive_unit(packet: UnitOperationPacket) -> bool:
    return packet.unit_type in {"reactor"} or packet.unit_id in {"reactor"}


def build_unit_composition_artifacts(
    streams: list[StreamRecord],
    packets: list[UnitOperationPacket],
    citations: list[str],
    assumptions: list[str],
) -> tuple[list[UnitCompositionState], list[CompositionClosure]]:
    stream_index = {stream.stream_id: stream for stream in streams}
    states: list[UnitCompositionState] = []
    closures: list[CompositionClosure] = []

    for packet in packets:
        inlet_streams = [stream_index[stream_id] for stream_id in packet.inlet_stream_ids if stream_id in stream_index]
        outlet_streams = [stream_index[stream_id] for stream_id in packet.outlet_stream_ids if stream_id in stream_index]
        inlet_molar = _aggregate_molar(inlet_streams)
        outlet_molar = _aggregate_molar(outlet_streams)
        inlet_mass = _aggregate_mass(inlet_streams)
        outlet_mass = _aggregate_mass(outlet_streams)
        inlet_mole_fraction = _normalize(inlet_molar)
        outlet_mole_fraction = _normalize(outlet_molar)
        inlet_mass_fraction = _normalize(inlet_mass)
        outlet_mass_fraction = _normalize(outlet_mass)
        notes: list[str] = []
        if not inlet_molar:
            notes.append("No inlet composition state is available from solved inlet streams.")
        if not outlet_molar:
            notes.append("No outlet composition state is available from solved outlet streams.")
        if packet.coverage_status != "complete":
            notes.append(f"Unit packet coverage is {packet.coverage_status}.")

        inlet_fraction_sum = round(sum(inlet_mole_fraction.values()), 6)
        outlet_fraction_sum = round(sum(outlet_mole_fraction.values()), 6)
        new_outlet = sorted(set(outlet_molar) - set(inlet_molar))
        missing_outlet = sorted(set(inlet_molar) - set(outlet_molar))
        reactive = _is_reactive_unit(packet)
        composition_error_pct = round(max(abs(1.0 - inlet_fraction_sum), abs(1.0 - outlet_fraction_sum)) * 100.0, 6)

        if not inlet_molar or not outlet_molar:
            status = "blocked"
        elif composition_error_pct <= 1.0 and (reactive or (not new_outlet and not missing_outlet)):
            status = "converged"
        elif composition_error_pct <= 5.0:
            status = "estimated"
        else:
            status = "blocked"

        closure_notes = list(notes)
        if reactive and (new_outlet or missing_outlet):
            closure_notes.append("Reactive unit allows transformed component sets between inlet and outlet.")
        elif new_outlet or missing_outlet:
            closure_notes.append(
                f"Non-reactive unit has component-set drift: new={', '.join(new_outlet[:4]) or '-'}; missing={', '.join(missing_outlet[:4]) or '-'}."
            )

        states.append(
            UnitCompositionState(
                state_id=f"{packet.unit_id}_composition_state",
                unit_id=packet.unit_id,
                unit_type=packet.unit_type,
                inlet_stream_ids=packet.inlet_stream_ids,
                outlet_stream_ids=packet.outlet_stream_ids,
                inlet_component_molar_kmol_hr=inlet_molar,
                outlet_component_molar_kmol_hr=outlet_molar,
                inlet_component_mass_kg_hr=inlet_mass,
                outlet_component_mass_kg_hr=outlet_mass,
                inlet_component_mole_fraction=inlet_mole_fraction,
                outlet_component_mole_fraction=outlet_mole_fraction,
                inlet_component_mass_fraction=inlet_mass_fraction,
                outlet_component_mass_fraction=outlet_mass_fraction,
                dominant_inlet_phase=_dominant_phase(inlet_streams),
                dominant_outlet_phase=_dominant_phase(outlet_streams),
                status=status,
                notes=notes,
                citations=citations,
                assumptions=assumptions,
            )
        )
        closures.append(
            CompositionClosure(
                closure_id=f"{packet.unit_id}_composition_closure",
                unit_id=packet.unit_id,
                reactive=reactive,
                inlet_fraction_sum=inlet_fraction_sum,
                outlet_fraction_sum=outlet_fraction_sum,
                new_outlet_components=new_outlet,
                missing_outlet_components=missing_outlet,
                composition_error_pct=composition_error_pct,
                closure_status=status,
                notes=closure_notes,
                citations=citations,
                assumptions=assumptions,
            )
        )
    return states, closures


def composition_state_for_unit(
    states: list[UnitCompositionState],
    *,
    unit_ids: tuple[str, ...] = (),
    unit_types: tuple[str, ...] = (),
) -> UnitCompositionState | None:
    for state in states:
        if unit_ids and state.unit_id in unit_ids:
            return state
        if unit_types and state.unit_type in unit_types:
            return state
    return None


def dominant_components(
    state: UnitCompositionState | None,
    *,
    side: str = "outlet",
    basis: str = "mole",
    limit: int = 3,
) -> list[tuple[str, float]]:
    if state is None:
        return []
    if side == "inlet":
        fractions = state.inlet_component_mole_fraction if basis == "mole" else state.inlet_component_mass_fraction
    else:
        fractions = state.outlet_component_mole_fraction if basis == "mole" else state.outlet_component_mass_fraction
    return sorted(fractions.items(), key=lambda item: item[1], reverse=True)[:limit]


def component_mass_fraction(state: UnitCompositionState | None, component_name: str, *, side: str = "outlet") -> float:
    if state is None:
        return 0.0
    fractions = state.outlet_component_mass_fraction if side == "outlet" else state.inlet_component_mass_fraction
    return fractions.get(component_name, 0.0)


def estimate_bulk_cp_kj_kg_k(state: UnitCompositionState | None, default: float = 2.5) -> float:
    if state is None:
        return default
    water_fraction = max(
        state.inlet_component_mass_fraction.get("Water", 0.0),
        state.outlet_component_mass_fraction.get("Water", 0.0),
    )
    dominant_phase = state.dominant_outlet_phase or state.dominant_inlet_phase
    if dominant_phase == "solid":
        return round(1.35 + water_fraction * 0.6, 3)
    if dominant_phase == "gas":
        return round(1.55 + water_fraction * 0.2, 3)
    if dominant_phase == "slurry":
        return round(2.00 + water_fraction * 1.2, 3)
    return round(2.20 + water_fraction * 1.8, 3)


def estimate_bulk_density_kg_m3(state: UnitCompositionState | None, default: float = 950.0) -> float:
    if state is None:
        return default
    dominant_phase = state.dominant_outlet_phase or state.dominant_inlet_phase
    water_fraction = max(
        state.inlet_component_mass_fraction.get("Water", 0.0),
        state.outlet_component_mass_fraction.get("Water", 0.0),
    )
    if dominant_phase == "gas":
        return 4.0
    if dominant_phase == "solid":
        return round(1050.0 + water_fraction * 150.0, 3)
    if dominant_phase == "slurry":
        return round(1150.0 + water_fraction * 180.0, 3)
    return round(820.0 + water_fraction * 260.0, 3)


def estimate_bulk_viscosity_pa_s(state: UnitCompositionState | None, default: float = 0.0020) -> float:
    if state is None:
        return default
    dominant_phase = state.dominant_outlet_phase or state.dominant_inlet_phase
    water_fraction = max(
        state.inlet_component_mass_fraction.get("Water", 0.0),
        state.outlet_component_mass_fraction.get("Water", 0.0),
    )
    if dominant_phase == "gas":
        return 2.0e-5
    if dominant_phase == "solid":
        return 0.0045
    if dominant_phase == "slurry":
        return round(0.0030 - min(water_fraction * 0.0012, 0.0010), 6)
    return round(0.0024 - min(water_fraction * 0.0012, 0.0010), 6)


def light_heavy_keys(state: UnitCompositionState | None) -> tuple[str, str]:
    ranked = dominant_components(state, side="outlet", basis="mole", limit=4)
    if not ranked:
        return "Light key", "Heavy key"
    names = [name for name, _ in ranked]
    lowered = {name: name.lower() for name in names}
    light = next((name for name in names if lowered[name] in {"water", "co2", "carbon dioxide", "sulfur dioxide", "methanol"}), names[0])
    heavy = next((name for name in reversed(names) if name != light), names[0])
    return light, heavy
