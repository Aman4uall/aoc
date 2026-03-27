from __future__ import annotations

from aoc.models import PhaseSplitSpec, SeparationPacket, SeparatorPerformance, StreamRecord, UnitOperationPacket
from aoc.properties.models import PropertyPackageArtifact
from aoc.properties.sources import normalize_chemical_name


def _henry_lookup(
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
            if item.gas_component_id == gas_id and item.solvent_component_id == solvent_id
        ),
        None,
    )


def _solubility_lookup(
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
            if item.solute_component_id == solute_id and item.solvent_component_id == solvent_id
        ),
        None,
    )


def henry_retained_fraction_to_liquid(
    gas_name: str,
    solvent_name: str,
    gas_molar_flow_kmol_hr: float,
    solvent_molar_flow_kmol_hr: float,
    partial_pressure_bar: float,
    property_packages: PropertyPackageArtifact | None,
) -> tuple[float, str, list[str], bool, str]:
    constant = _henry_lookup(property_packages, gas_name, solvent_name)
    if (
        constant is None
        or constant.resolution_status != "resolved"
        or gas_molar_flow_kmol_hr <= 1e-12
        or solvent_molar_flow_kmol_hr <= 1e-12
    ):
        return 0.0, "heuristic_gle_fallback", [], True, (
            f"No cited Henry's-law constant resolved for {gas_name} in {solvent_name}; absorber/stripper split falls back to the existing heuristic basis."
        )
    henry_bar = max(constant.value, 1e-9)
    x_eq = max(min(partial_pressure_bar / henry_bar, 0.85), 0.0)
    max_dissolved = (x_eq / max(1.0 - x_eq, 1e-9)) * solvent_molar_flow_kmol_hr
    retained_fraction = max(min(max_dissolved / gas_molar_flow_kmol_hr, 1.0), 0.0)
    return retained_fraction, "henry_law", [constant.constant_id], False, (
        f"Gas retention for {gas_name} in {solvent_name} is screened with Henry's law (P = Hx)."
    )


def solubility_limit_kg_per_kg_solvent(
    solute_name: str,
    solvent_name: str,
    temperature_c: float,
    property_packages: PropertyPackageArtifact | None,
) -> tuple[float | None, str, list[str], bool, str]:
    curve = _solubility_lookup(property_packages, solute_name, solvent_name)
    if curve is None or curve.resolution_status != "resolved":
        return None, "heuristic_sle_fallback", [], True, (
            f"No cited solubility curve resolved for {solute_name} in {solvent_name}; crystallization/filter split falls back to the existing heuristic basis."
        )
    if curve.equation_name.lower() == "linear":
        a = float(curve.parameters.get("a", 0.0))
        b = float(curve.parameters.get("b", 0.0))
        value = a + b * temperature_c
    else:
        value = None
    if value is None:
        return None, "heuristic_sle_fallback", [curve.curve_id], True, (
            f"Unsupported solubility equation '{curve.equation_name}' for {solute_name} in {solvent_name}; heuristic split retained."
        )
    return max(value, 0.0), "solubility_curve", [curve.curve_id], False, (
        f"Solubility limit for {solute_name} in {solvent_name} is evaluated from the resolved {curve.equation_name} curve."
    )


SEPARATION_UNIT_TYPES = {
    "flash",
    "distillation",
    "absorption",
    "stripping",
    "extraction",
    "crystallization",
    "filtration",
    "drying",
    "evaporation",
    "separation",
}


def _aggregate_component_molar(streams: list[StreamRecord], stream_ids: list[str]) -> dict[str, float]:
    selected_ids = set(stream_ids)
    state: dict[str, float] = {}
    for stream in streams:
        if stream.stream_id not in selected_ids:
            continue
        for component in stream.components:
            state[component.name] = state.get(component.name, 0.0) + component.molar_flow_kmol_hr
    return state


def _aggregate_mass(streams: list[StreamRecord], stream_ids: list[str]) -> float:
    selected_ids = set(stream_ids)
    return sum(
        component.mass_flow_kg_hr
        for stream in streams
        if stream.stream_id in selected_ids
        for component in stream.components
    )


def _aggregate_phases(streams: list[StreamRecord], stream_ids: list[str]) -> list[str]:
    selected_ids = set(stream_ids)
    phases = {
        (stream.phase_hint or "mixed")
        for stream in streams
        if stream.stream_id in selected_ids
    }
    return sorted(phases)


def _dominant_phase(streams: list[StreamRecord], stream_ids: list[str]) -> str:
    selected_ids = set(stream_ids)
    phase_totals: dict[str, float] = {}
    for stream in streams:
        if stream.stream_id not in selected_ids:
            continue
        total_mass = sum(component.mass_flow_kg_hr for component in stream.components)
        phase = stream.phase_hint or "mixed"
        phase_totals[phase] = phase_totals.get(phase, 0.0) + total_mass
    if not phase_totals:
        return ""
    return max(phase_totals.items(), key=lambda item: item[1])[0]


def _component_split_fractions(inlet_state: dict[str, float], outlet_state: dict[str, float]) -> dict[str, float]:
    split: dict[str, float] = {}
    for component_name, inlet_molar in inlet_state.items():
        if inlet_molar <= 1e-10:
            continue
        split[component_name] = round(outlet_state.get(component_name, 0.0) / inlet_molar, 6)
    return split


def _infer_split_basis(unit_type: str, family: str) -> tuple[str, str, str]:
    if unit_type in {"flash", "distillation", "evaporation"}:
        return "temperature/volatility", "vapor_liquid_equilibrium", "temperature/volatility"
    if unit_type in {"absorption", "stripping"}:
        return "gas-liquid mass transfer", "gas_liquid_partition", "solubility/phase split"
    if unit_type == "extraction":
        return "liquid-liquid partition", "liquid_liquid_partition", "solubility/phase split"
    if unit_type in {"crystallization", "filtration"}:
        return "solid-liquid partition", "solid_liquid_partition", "solubility/phase split"
    if unit_type == "drying":
        return "moisture removal", "solid_vapor_partition", "temperature/volatility"
    if family == "solids":
        return "solid-liquid partition", "solid_liquid_partition", "solubility/phase split"
    return "heuristic partition", "heuristic_split", "solubility/phase split"


def _outlet_groups(streams: list[StreamRecord], unit_id: str) -> tuple[list[str], list[str], list[str], list[str]]:
    outlet_streams = [stream for stream in streams if stream.source_unit_id == unit_id]
    product_stream_ids = [stream.stream_id for stream in outlet_streams if stream.destination_unit_id not in {"feed_prep", "waste_treatment"}]
    waste_stream_ids = [stream.stream_id for stream in outlet_streams if stream.destination_unit_id == "waste_treatment"]
    recycle_stream_ids = [stream.stream_id for stream in outlet_streams if stream.destination_unit_id == "feed_prep"]
    side_draw_stream_ids = [
        stream.stream_id
        for stream in outlet_streams
        if stream.stream_id not in product_stream_ids and stream.stream_id not in waste_stream_ids and stream.stream_id not in recycle_stream_ids
    ]
    return product_stream_ids, waste_stream_ids, recycle_stream_ids, side_draw_stream_ids


def _performance_status(split_closure_pct: float, phase_status: str, has_outlets: bool) -> str:
    if not has_outlets or phase_status == "blocked":
        return "blocked"
    if split_closure_pct <= 5.0 and phase_status == "complete":
        return "converged"
    if split_closure_pct <= 25.0:
        return "estimated"
    return "blocked"


def build_separator_models(
    streams: list[StreamRecord],
    family: str,
    unit_packets: list[UnitOperationPacket],
    citations: list[str],
    assumptions: list[str],
    property_packages: PropertyPackageArtifact | None = None,
    component_package_ids: dict[str, str] | None = None,
) -> tuple[list[PhaseSplitSpec], list[SeparatorPerformance], list[SeparationPacket]]:
    packet_index = {packet.unit_id: packet for packet in unit_packets if packet.unit_type in SEPARATION_UNIT_TYPES}
    phase_split_specs: list[PhaseSplitSpec] = []
    separator_performances: list[SeparatorPerformance] = []
    separation_packets: list[SeparationPacket] = []

    for unit_id, packet in packet_index.items():
        product_stream_ids, waste_stream_ids, recycle_stream_ids, side_draw_stream_ids = _outlet_groups(streams, unit_id)
        inlet_stream_ids = packet.inlet_stream_ids
        inlet_state = _aggregate_component_molar(streams, inlet_stream_ids)
        product_state = _aggregate_component_molar(streams, product_stream_ids)
        waste_state = _aggregate_component_molar(streams, waste_stream_ids)
        recycle_state = _aggregate_component_molar(streams, recycle_stream_ids)
        side_draw_state = _aggregate_component_molar(streams, side_draw_stream_ids)

        split_basis, mechanism, driving_force = _infer_split_basis(packet.unit_type, family)
        inlet_phases = _aggregate_phases(streams, inlet_stream_ids)
        product_phase = _dominant_phase(streams, product_stream_ids)
        waste_phase = _dominant_phase(streams, waste_stream_ids)
        recycle_phase = _dominant_phase(streams, recycle_stream_ids)
        side_draw_phase = _dominant_phase(streams, side_draw_stream_ids)

        phase_notes: list[str] = []
        equilibrium_model = ""
        equilibrium_parameter_ids: list[str] = []
        equilibrium_fallback = False
        if not inlet_stream_ids:
            phase_notes.append("No inlet streams resolved for this separator.")
        if not (product_stream_ids or waste_stream_ids or recycle_stream_ids or side_draw_stream_ids):
            phase_notes.append("No resolved outlet streams for this separator.")
        if "mixed" in inlet_phases:
            phase_notes.append("Inlet stream phase basis remains mixed and should be refined.")
        if any(not phase for phase in [product_phase if product_stream_ids else "ok", waste_phase if waste_stream_ids else "ok", recycle_phase if recycle_stream_ids else "ok"]):
            phase_notes.append("One or more separator outlet phases could not be resolved.")
        inlet_component_names = list(inlet_state)
        if packet.unit_type in {"absorption", "stripping"} and property_packages is not None:
            solvent_candidates = [name for name in inlet_component_names if normalize_chemical_name(name) in {"water", "sulfuric_acid", "spent_acid"}]
            gas_candidates = [name for name in inlet_component_names if normalize_chemical_name(name) in {"sulfur_dioxide", "carbon_dioxide", "ammonia", "oxygen"}]
            for gas_name in gas_candidates:
                for solvent_name in solvent_candidates:
                    constant = _henry_lookup(property_packages, gas_name, solvent_name)
                    if constant is not None and constant.resolution_status == "resolved":
                        equilibrium_model = "henry_law"
                        equilibrium_parameter_ids.append(constant.constant_id)
                        phase_notes.append(f"GLE basis uses Henry's law for {gas_name} in {solvent_name}.")
                        break
                if equilibrium_model == "henry_law":
                    break
            if not equilibrium_model and gas_candidates and solvent_candidates:
                equilibrium_model = "heuristic_gle_fallback"
                equilibrium_fallback = True
                phase_notes.append("No cited Henry's-law pair was resolved for the active absorber/stripper components; heuristic split retained.")
        if packet.unit_type in {"crystallization", "filtration"} and property_packages is not None:
            solvent_candidates = [name for name in inlet_component_names if normalize_chemical_name(name) == "water"]
            solid_candidates = [
                name
                for name in inlet_component_names
                if normalize_chemical_name(name) in {"sodium_bicarbonate", "soda_ash", "sodium_hydroxide", "sodium_chloride"}
            ]
            for solute_name in solid_candidates:
                for solvent_name in solvent_candidates:
                    curve = _solubility_lookup(property_packages, solute_name, solvent_name)
                    if curve is not None and curve.resolution_status == "resolved":
                        equilibrium_model = "solubility_curve"
                        equilibrium_parameter_ids.append(curve.curve_id)
                        phase_notes.append(f"SLE basis uses a solubility curve for {solute_name} in {solvent_name}.")
                        break
                if equilibrium_model == "solubility_curve":
                    break
            if not equilibrium_model and solid_candidates and solvent_candidates:
                equilibrium_model = "heuristic_sle_fallback"
                equilibrium_fallback = True
                phase_notes.append("No cited solubility curve was resolved for the active crystal/slurry system; heuristic split retained.")
        phase_status = (
            "blocked"
            if not inlet_stream_ids or not (product_stream_ids or waste_stream_ids or recycle_stream_ids or side_draw_stream_ids)
            else "partial"
            if phase_notes
            else "complete"
        )
        spec = PhaseSplitSpec(
            spec_id=f"{unit_id}_phase_split_spec",
            unit_id=unit_id,
            separation_family=packet.unit_type,
            split_basis=split_basis,
            mechanism=mechanism,
            inlet_phases=inlet_phases,
            product_phase_target=product_phase,
            waste_phase_target=waste_phase,
            recycle_phase_target=recycle_phase,
            side_draw_phase_target=side_draw_phase,
            equilibrium_model=equilibrium_model,
            equilibrium_parameter_ids=equilibrium_parameter_ids,
            equilibrium_fallback=equilibrium_fallback,
            phase_split_status=phase_status,
            notes=phase_notes,
            citations=citations,
            assumptions=assumptions,
        )
        phase_split_specs.append(spec)

        product_split = _component_split_fractions(inlet_state, product_state)
        waste_split = _component_split_fractions(inlet_state, waste_state)
        recycle_split = _component_split_fractions(inlet_state, recycle_state)
        side_draw_split = _component_split_fractions(inlet_state, side_draw_state)
        component_names = set(product_split) | set(waste_split) | set(recycle_split) | set(side_draw_split)
        split_closure_pct = max(
            (
                abs(
                    1.0
                    - (
                        product_split.get(name, 0.0)
                        + waste_split.get(name, 0.0)
                        + recycle_split.get(name, 0.0)
                        + side_draw_split.get(name, 0.0)
                    )
                )
                * 100.0
                for name in component_names
            ),
            default=0.0,
        )
        inlet_mass = max(_aggregate_mass(streams, inlet_stream_ids), 1e-9)
        performance_notes = list(phase_notes)
        if split_closure_pct > 5.0:
            performance_notes.append(f"Split closure drifts by {split_closure_pct:.3f}% across one or more components.")
        if component_package_ids:
            matched = sum(1 for name in inlet_state if name in component_package_ids)
            performance_notes.append(
                f"Separator model is prepared for future property-package coupling; matched component identifiers: {matched}."
            )
        performance = SeparatorPerformance(
            performance_id=f"{unit_id}_separator_performance",
            unit_id=unit_id,
            separation_family=packet.unit_type,
            inlet_stream_ids=inlet_stream_ids,
            product_stream_ids=product_stream_ids,
            waste_stream_ids=waste_stream_ids,
            recycle_stream_ids=recycle_stream_ids,
            side_draw_stream_ids=side_draw_stream_ids,
            component_split_to_product=product_split,
            component_split_to_waste=waste_split,
            component_split_to_recycle=recycle_split,
            dominant_product_phase=product_phase,
            dominant_waste_phase=waste_phase,
            dominant_recycle_phase=recycle_phase,
            product_mass_fraction=round(_aggregate_mass(streams, product_stream_ids) / inlet_mass, 6),
            waste_mass_fraction=round(_aggregate_mass(streams, waste_stream_ids) / inlet_mass, 6),
            recycle_mass_fraction=round(_aggregate_mass(streams, recycle_stream_ids) / inlet_mass, 6),
            side_draw_mass_fraction=round(_aggregate_mass(streams, side_draw_stream_ids) / inlet_mass, 6),
            split_closure_pct=round(split_closure_pct, 6),
            equilibrium_model=equilibrium_model,
            equilibrium_parameter_ids=equilibrium_parameter_ids,
            equilibrium_fallback=equilibrium_fallback,
            performance_status=_performance_status(split_closure_pct, phase_status, bool(product_stream_ids or waste_stream_ids or recycle_stream_ids or side_draw_stream_ids)),
            notes=performance_notes,
            citations=citations,
            assumptions=assumptions,
        )
        separator_performances.append(performance)

        separation_packets.append(
            SeparationPacket(
                packet_id=f"{unit_id}_separation_packet",
                unit_id=unit_id,
                separation_family=packet.unit_type,
                driving_force=driving_force,
                inlet_stream_ids=inlet_stream_ids,
                product_stream_ids=product_stream_ids,
                waste_stream_ids=waste_stream_ids,
                recycle_stream_ids=recycle_stream_ids,
                side_draw_stream_ids=side_draw_stream_ids,
                phase_split_spec_id=spec.spec_id,
                separator_performance_id=performance.performance_id,
                split_basis=spec.split_basis,
                component_split_to_product=product_split,
                component_split_to_waste=waste_split,
                component_split_to_recycle=recycle_split,
                dominant_product_phase=product_phase,
                dominant_waste_phase=waste_phase,
                dominant_recycle_phase=recycle_phase,
                product_mass_fraction=performance.product_mass_fraction,
                waste_mass_fraction=performance.waste_mass_fraction,
                recycle_mass_fraction=performance.recycle_mass_fraction,
                side_draw_mass_fraction=performance.side_draw_mass_fraction,
                split_closure_pct=performance.split_closure_pct,
                equilibrium_model=equilibrium_model,
                equilibrium_parameter_ids=equilibrium_parameter_ids,
                equilibrium_fallback=equilibrium_fallback,
                split_status=performance.performance_status,
                closure_error_pct=packet.closure_error_pct,
                notes=performance.notes,
                citations=citations,
                assumptions=assumptions,
            )
        )

    return phase_split_specs, separator_performances, separation_packets
