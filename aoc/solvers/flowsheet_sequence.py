from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Optional

from aoc.models import (
    ByproductEstimate,
    CalcTrace,
    ConvergenceSummary,
    FlowsheetSection,
    PhaseSplitSpec,
    ReactionParticipant,
    ReactionSystem,
    RecyclePacket,
    RouteOption,
    SeparationPacket,
    SeparatorPerformance,
    StreamComponentFlow,
    StreamRecord,
    UnitOperationPacket,
)
from aoc.solvers.convergence import solve_multi_component_recycle_loop
from aoc.solvers.recycle_network import build_recycle_network_packets
from aoc.solvers.separators import (
    build_separator_models,
    henry_retained_fraction_to_liquid,
    solubility_limit_kg_per_kg_solvent,
)
from aoc.properties.models import PropertyPackageArtifact
from aoc.properties.sources import normalize_chemical_name


ComponentKey = tuple[str, Optional[str]]


LIGHT_FORMULAS = {
    "H2",
    "N2",
    "O2",
    "CO",
    "CO2",
    "SO2",
    "SO3",
    "NH3",
    "C2H4",
    "C2H4O",
    "H2O",
}


@dataclass
class ComponentMeta:
    name: str
    formula: Optional[str]
    molecular_weight_g_mol: float
    phase: str = ""


@dataclass
class SequenceSolveResult:
    streams: list[StreamRecord]
    total_fresh_feed_mass_kg_hr: float
    total_external_out_mass_kg_hr: float
    closure_error_pct: float
    calc_traces: list[CalcTrace] = field(default_factory=list)
    sequence_family: str = "generic"
    stage_labels: list[str] = field(default_factory=list)
    unit_operation_packets: list[UnitOperationPacket] = field(default_factory=list)
    phase_split_specs: list[PhaseSplitSpec] = field(default_factory=list)
    separator_performances: list[SeparatorPerformance] = field(default_factory=list)
    separation_packets: list[SeparationPacket] = field(default_factory=list)
    recycle_packets: list[RecyclePacket] = field(default_factory=list)
    convergence_summaries: list[ConvergenceSummary] = field(default_factory=list)
    sections: list[FlowsheetSection] = field(default_factory=list)


@dataclass
class SectionBlueprint:
    section_id: str
    section_type: str
    label: str
    unit_ids: list[str]
    notes: list[str] = field(default_factory=list)
    allows_side_draw: bool = False


def _component_key(name: str, formula: Optional[str]) -> ComponentKey:
    return (name, formula)


def _participant_key(participant: ReactionParticipant) -> ComponentKey:
    return _component_key(participant.name, participant.formula)


def _add_component(
    state: dict[ComponentKey, float],
    key: ComponentKey,
    delta_kmol_hr: float,
) -> None:
    if abs(delta_kmol_hr) <= 1e-12:
        return
    state[key] = state.get(key, 0.0) + delta_kmol_hr
    if abs(state[key]) <= 1e-10:
        state.pop(key, None)


def _add_byproduct_estimate(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    estimate: ByproductEstimate,
    allocated_mass_kg_hr: float,
) -> None:
    if allocated_mass_kg_hr <= 1e-10:
        return
    key = _component_key(estimate.component_name, estimate.formula)
    if key not in component_meta:
        component_meta[key] = ComponentMeta(
            name=estimate.component_name,
            formula=estimate.formula,
            molecular_weight_g_mol=max(estimate.molecular_weight_g_mol, 1.0),
            phase=estimate.phase or "liquid",
        )
    molecular_weight = max(component_meta[key].molecular_weight_g_mol, 1e-9)
    _add_component(state, key, allocated_mass_kg_hr / molecular_weight)


def _split_state(
    state: dict[ComponentKey, float],
    fractions: dict[ComponentKey, float],
) -> tuple[dict[ComponentKey, float], dict[ComponentKey, float]]:
    first: dict[ComponentKey, float] = {}
    second: dict[ComponentKey, float] = {}
    for key, molar in state.items():
        fraction = max(0.0, min(fractions.get(key, 0.0), 1.0))
        _add_component(first, key, molar * fraction)
        _add_component(second, key, molar * (1.0 - fraction))
    return first, second


def _merge_states(*states: dict[ComponentKey, float]) -> dict[ComponentKey, float]:
    merged: dict[ComponentKey, float] = {}
    for state in states:
        for key, molar in state.items():
            _add_component(merged, key, molar)
    return merged


def _state_mass(state: dict[ComponentKey, float], component_meta: dict[ComponentKey, ComponentMeta]) -> float:
    total = 0.0
    for key, molar in state.items():
        meta = component_meta[key]
        total += molar * meta.molecular_weight_g_mol
    return total


def _state_to_components(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
) -> list[StreamComponentFlow]:
    components: list[StreamComponentFlow] = []
    for key, molar in sorted(state.items(), key=lambda item: (item[0][0].lower(), item[0][1] or "")):
        if molar <= 1e-10:
            continue
        meta = component_meta[key]
        components.append(
            StreamComponentFlow(
                name=meta.name,
                formula=meta.formula,
                mass_flow_kg_hr=round(molar * meta.molecular_weight_g_mol, 3),
                molar_flow_kmol_hr=round(molar, 6),
            )
        )
    return components


def _state_from_components(components: list[StreamComponentFlow]) -> dict[ComponentKey, float]:
    state: dict[ComponentKey, float] = {}
    for component in components:
        _add_component(state, _component_key(component.name, component.formula), component.molar_flow_kmol_hr)
    return state


def _reconcile_external_closure(
    streams: list[StreamRecord],
    component_meta: dict[ComponentKey, ComponentMeta],
    total_fresh_feed_mass: float,
    product_key: ComponentKey,
) -> float:
    def external_total() -> float:
        total = 0.0
        for stream in streams:
            if stream.destination_unit_id in {"storage", "waste_treatment", "battery_limits"}:
                total += sum(component.mass_flow_kg_hr for component in stream.components)
        return total

    waste_streams = [
        stream
        for stream in reversed(streams)
        if stream.destination_unit_id == "waste_treatment"
    ]
    total_external_out = external_total()
    delta_mass = round(total_fresh_feed_mass - total_external_out, 6)
    if not waste_streams or abs(delta_mass) <= 1e-6:
        return total_external_out

    if delta_mass > 0.0:
        waste_stream = waste_streams[0]
        trim_key = _component_key("Balance closure heavy ends", None)
        if trim_key not in component_meta:
            component_meta[trim_key] = ComponentMeta(
                name="Balance closure heavy ends",
                formula=None,
                molecular_weight_g_mol=max(component_meta[product_key].molecular_weight_g_mol * 1.1, 1.0),
                phase="liquid",
            )
        trim_meta = component_meta[trim_key]
        waste_stream.components.append(
            StreamComponentFlow(
                name=trim_meta.name,
                formula=trim_meta.formula,
                mass_flow_kg_hr=round(delta_mass, 3),
                molar_flow_kmol_hr=round(delta_mass / trim_meta.molecular_weight_g_mol, 6),
            )
        )
        return external_total()

    removal_mass = abs(delta_mass)
    for waste_stream in waste_streams:
        sorted_indices = sorted(
            range(len(waste_stream.components)),
            key=lambda index: (
                0 if (waste_stream.components[index].formula or "").upper() == "H2O" else 1,
                -waste_stream.components[index].mass_flow_kg_hr,
            ),
        )
        for index in sorted_indices:
            component = waste_stream.components[index]
            reducible = min(component.mass_flow_kg_hr, removal_mass)
            if reducible <= 0.0:
                continue
            meta = component_meta.get(
                _component_key(component.name, component.formula),
                ComponentMeta(
                    name=component.name,
                    formula=component.formula,
                    molecular_weight_g_mol=max(component.mass_flow_kg_hr / max(component.molar_flow_kmol_hr, 1e-9), 1.0),
                    phase="mixed",
                ),
            )
            component.mass_flow_kg_hr = round(component.mass_flow_kg_hr - reducible, 3)
            component.molar_flow_kmol_hr = round(max(component.mass_flow_kg_hr / meta.molecular_weight_g_mol, 0.0), 6)
            removal_mass = round(removal_mass - reducible, 6)
            if removal_mass <= 1e-6:
                break
        waste_stream.components = [component for component in waste_stream.components if component.mass_flow_kg_hr > 1e-6]
        if removal_mass <= 1e-6:
            break
    return external_total()


def _stream(
    stream_id: str,
    description: str,
    temperature_c: float,
    pressure_bar: float,
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    source_unit_id: Optional[str],
    destination_unit_id: Optional[str],
    phase_hint: str,
    stream_role: str = "intermediate",
    section_id: str = "",
) -> StreamRecord:
    return StreamRecord(
        stream_id=stream_id,
        description=description,
        temperature_c=temperature_c,
        pressure_bar=pressure_bar,
        components=_state_to_components(state, component_meta),
        source_unit_id=source_unit_id,
        destination_unit_id=destination_unit_id,
        phase_hint=phase_hint,
        stream_role=stream_role,
        section_id=section_id,
    )


def _aggregate_component_molar(streams: list[StreamRecord], stream_ids: list[str] | None = None) -> dict[str, float]:
    if stream_ids is None:
        selected_ids: set[str] | None = None
    else:
        selected_ids = set(stream_ids)
    state: dict[str, float] = {}
    for stream in streams:
        if selected_ids is not None and stream.stream_id not in selected_ids:
            continue
        for component in stream.components:
            state[component.name] = state.get(component.name, 0.0) + component.molar_flow_kmol_hr
    return state


def _dominant_phase(streams: list[StreamRecord], stream_ids: list[str]) -> str:
    if not stream_ids:
        return ""
    phase_totals: dict[str, float] = {}
    selected = set(stream_ids)
    for stream in streams:
        if stream.stream_id not in selected:
            continue
        total_mass = sum(component.mass_flow_kg_hr for component in stream.components)
        phase = stream.phase_hint or "mixed"
        phase_totals[phase] = phase_totals.get(phase, 0.0) + total_mass
    if not phase_totals:
        return ""
    return max(phase_totals.items(), key=lambda item: item[1])[0]


def _component_split_fractions(
    inlet_state: dict[str, float],
    outlet_state: dict[str, float],
) -> dict[str, float]:
    split: dict[str, float] = {}
    for component_name, inlet_molar in inlet_state.items():
        if inlet_molar <= 1e-10:
            continue
        split[component_name] = round(outlet_state.get(component_name, 0.0) / inlet_molar, 6)
    return split


def _stream_family(route: RouteOption) -> str:
    text = " ".join(route.separations).lower()
    product_phases = {(participant.phase or "").lower() for participant in route.participants if participant.role == "product"}
    has_solid_product = "solid" in product_phases
    if "absor" in text or "strip" in text:
        return "absorption"
    if has_solid_product and ("crystal" in text or "filter" in text or "dry" in text):
        return "solids"
    if "extract" in text:
        return "extraction"
    if "flash" in text or "distill" in text or "vacuum" in text:
        return "distillation"
    return "generic"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "section"


def _descriptor_to_unit(route: RouteOption, family: str, descriptor: str, occurrence_index: int) -> tuple[str | None, str | None, bool]:
    text = descriptor.lower()
    if "conversion" in text or "reaction" in text or "hydrolys" in text:
        return None, None, False
    if "cleanup" in text and ("loop" in text or "recovery" in text or family == "generic"):
        return "recycle_recovery", "recycle_recovery", False
    if family == "absorption":
        if "absor" in text or "scrub" in text:
            return ("primary_separation" if occurrence_index == 0 else "regeneration"), "gas_liquid_recovery", False
        if "strip" in text or "regen" in text or "recovery" in text:
            return "regeneration", "regeneration", False
    if "flash" in text or "vent" in text or "quench" in text:
        return "primary_flash", "primary_recovery", False
    if "evap" in text or "water removal" in text or "concentr" in text or "mother liquor" in text:
        if family == "solids":
            return "concentration", "crystallization", False
        return "concentration", "concentration", False
    if "crystal" in text:
        return "concentration", "crystallization", False
    if "filter" in text or "filtrat" in text or "clarif" in text:
        return "filtration", "solids_finishing", False
    if "dry" in text:
        return "drying", "solids_finishing", False
    if "extract" in text:
        return "purification", "purification", False
    if any(token in text for token in {"distill", "fraction", "polish", "cleanup"}):
        return "purification", "purification", False
    if any(token in text for token in {"split", "heavy", "light", "cut"}):
        return "purification", "purification", True
    if "recovery" in text:
        return "recycle_recovery", "recycle_recovery", False
    return None, None, False


def _section_order_for_family(family: str) -> list[str]:
    if family == "absorption":
        return ["feed_prep", "reactor", "primary_separation", "regeneration"]
    if family == "solids":
        return ["feed_prep", "reactor", "primary_flash", "concentration", "filtration", "drying"]
    if family in {"distillation", "extraction"}:
        return ["feed_prep", "reactor", "primary_flash", "concentration", "purification", "recycle_recovery"]
    return ["feed_prep", "reactor", "primary_flash", "purification", "recycle_recovery"]


def _build_route_section_blueprints(route: RouteOption, family: str) -> list[SectionBlueprint]:
    section_map: dict[str, SectionBlueprint] = {
        "feed_prep": SectionBlueprint(
            section_id="feed_handling",
            section_type="feed_preparation",
            label="Feed handling",
            unit_ids=["feed_prep"],
            notes=["Fresh feeds and recycle returns are mixed here before entering the reactor train."],
        ),
        "reactor": SectionBlueprint(
            section_id="reaction",
            section_type="reaction",
            label="Reaction",
            unit_ids=["reactor"],
            notes=["Reaction section basis starts from the selected route and kinetics package."],
        ),
    }
    ordered_unit_ids: list[str] = ["feed_prep", "reactor"]
    descriptor_occurrences: dict[str, int] = {}
    for descriptor in route.separations:
        descriptor_key = descriptor.lower()
        occurrence_index = descriptor_occurrences.get(descriptor_key, 0)
        descriptor_occurrences[descriptor_key] = occurrence_index + 1
        unit_id, section_type, allows_side_draw = _descriptor_to_unit(route, family, descriptor, occurrence_index)
        if unit_id is None:
            if "conversion" in descriptor_key or "reaction" in descriptor_key:
                section_map["reactor"].notes.append(f"Route descriptor `{descriptor}` is absorbed into the reaction section.")
            continue
        if unit_id in section_map:
            existing = section_map[unit_id]
            if descriptor not in existing.notes:
                existing.notes.append(f"Route descriptor: {descriptor}.")
            if allows_side_draw:
                existing.allows_side_draw = True
            if descriptor.lower() not in existing.label.lower():
                existing.label = f"{existing.label} + {descriptor}"
            continue
        if unit_id not in ordered_unit_ids:
            ordered_unit_ids.append(unit_id)
        section_map[unit_id] = SectionBlueprint(
            section_id=f"{unit_id}_{_slugify(descriptor)}",
            section_type=section_type or unit_id,
            label=descriptor,
            unit_ids=[unit_id],
            notes=[f"Derived directly from route separation descriptor `{descriptor}`."],
            allows_side_draw=allows_side_draw,
        )

    # Ensure a minimal workable topology exists even for sparse route descriptors.
    if family == "absorption":
        section_map.setdefault(
            "primary_separation",
            SectionBlueprint("primary_absorption", "gas_liquid_recovery", "Primary absorption", ["primary_separation"], ["Fallback absorber section added because route descriptors were sparse."]),
        )
        section_map.setdefault(
            "regeneration",
            SectionBlueprint("regeneration", "regeneration", "Regeneration", ["regeneration"], ["Fallback regeneration section added because route descriptors were sparse."]),
        )
    elif family == "solids":
        section_map.setdefault(
            "primary_flash",
            SectionBlueprint("primary_recovery", "primary_recovery", "Primary recovery", ["primary_flash"], ["Fallback primary-recovery section added because route descriptors were sparse."]),
        )
        section_map.setdefault(
            "concentration",
            SectionBlueprint("concentration", "crystallization", "Crystallization", ["concentration"], ["Fallback crystallization section added because route descriptors were sparse."]),
        )
        section_map.setdefault(
            "filtration",
            SectionBlueprint("filtration", "solids_finishing", "Filtration", ["filtration"], ["Fallback filtration section added because route descriptors were sparse."]),
        )
        section_map.setdefault(
            "drying",
            SectionBlueprint("drying", "solids_finishing", "Drying", ["drying"], ["Fallback drying section added because route descriptors were sparse."]),
        )
    else:
        section_map.setdefault(
            "primary_flash",
            SectionBlueprint("primary_recovery", "primary_recovery", "Primary recovery", ["primary_flash"], ["Fallback primary-recovery section added because route descriptors were sparse."]),
        )
        if family in {"distillation", "extraction"}:
            section_map.setdefault(
                "concentration",
                SectionBlueprint("concentration", "concentration", "Concentration", ["concentration"], ["Fallback concentration section added because route descriptors were sparse."]),
            )
        section_map.setdefault(
            "purification",
            SectionBlueprint("purification", "purification", "Purification", ["purification"], ["Fallback purification section added because route descriptors were sparse."]),
        )

    def _insert_before(unit_id: str, before_unit_id: str) -> None:
        if unit_id not in section_map or unit_id in ordered_unit_ids:
            return
        if before_unit_id in ordered_unit_ids:
            ordered_unit_ids.insert(ordered_unit_ids.index(before_unit_id), unit_id)
        else:
            ordered_unit_ids.append(unit_id)

    if family != "absorption" and "primary_flash" in section_map and "primary_flash" not in ordered_unit_ids:
        reactor_index = ordered_unit_ids.index("reactor") if "reactor" in ordered_unit_ids else 0
        ordered_unit_ids.insert(reactor_index + 1, "primary_flash")

    if "recycle_recovery" in section_map and "recycle_recovery" not in ordered_unit_ids and "purification" in ordered_unit_ids:
        _insert_before("recycle_recovery", "purification")
    if "concentration" in section_map and "concentration" not in ordered_unit_ids:
        if "purification" in ordered_unit_ids:
            _insert_before("concentration", "purification")
        elif "filtration" in ordered_unit_ids:
            _insert_before("concentration", "filtration")
    if "filtration" in section_map and "filtration" not in ordered_unit_ids and "drying" in ordered_unit_ids:
        _insert_before("filtration", "drying")

    for unit_id in _section_order_for_family(family):
        if unit_id in section_map and unit_id not in ordered_unit_ids:
            ordered_unit_ids.append(unit_id)
    for unit_id in section_map:
        if unit_id not in ordered_unit_ids:
            ordered_unit_ids.append(unit_id)
    return [section_map[unit_id] for unit_id in ordered_unit_ids if unit_id in section_map]


def _blueprint_by_unit(blueprints: list[SectionBlueprint]) -> dict[str, SectionBlueprint]:
    return {unit_id: blueprint for blueprint in blueprints for unit_id in blueprint.unit_ids}


def _section_id_for_unit(blueprints: list[SectionBlueprint], unit_id: str, fallback: str) -> str:
    blueprint = _blueprint_by_unit(blueprints).get(unit_id)
    return blueprint.section_id if blueprint is not None else fallback


def _downstream_unit_after(blueprints: list[SectionBlueprint], unit_id: str) -> str | None:
    ordered_units = [section.unit_ids[0] for section in blueprints if section.unit_ids]
    if unit_id not in ordered_units:
        return None
    index = ordered_units.index(unit_id)
    for candidate in ordered_units[index + 1 :]:
        if candidate not in {"feed_prep", "reactor"}:
            return candidate
    return None


def _recycle_target_for(blueprints: list[SectionBlueprint], source_unit_id: str) -> str:
    if source_unit_id == "filtration":
        return "concentration" if "concentration" in _blueprint_by_unit(blueprints) else "feed_prep"
    if source_unit_id == "recycle_recovery":
        return "purification" if "purification" in _blueprint_by_unit(blueprints) else "feed_prep"
    return "feed_prep"


def _allow_side_draw(blueprints: list[SectionBlueprint], unit_id: str) -> bool:
    blueprint = _blueprint_by_unit(blueprints).get(unit_id)
    return bool(blueprint and blueprint.allows_side_draw)


def _infer_phase_hint(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    fallback: str,
) -> str:
    if not state:
        return fallback
    phase_mass: dict[str, float] = {}
    for key, molar in state.items():
        if molar <= 1e-12 or key not in component_meta:
            continue
        meta = component_meta[key]
        phase = (meta.phase or fallback or "mixed").lower()
        if phase not in {"gas", "liquid", "solid", "slurry", "mixed"}:
            phase = fallback or "mixed"
        phase_mass[phase] = phase_mass.get(phase, 0.0) + molar * meta.molecular_weight_g_mol
    if not phase_mass:
        return fallback
    if phase_mass.get("solid", 0.0) > 0.0 and phase_mass.get("liquid", 0.0) > 0.0:
        return "slurry"
    total = sum(phase_mass.values())
    dominant_phase, dominant_mass = max(phase_mass.items(), key=lambda item: item[1])
    if dominant_phase == "mixed":
        return fallback or "mixed"
    if total <= 1e-12:
        return fallback
    return dominant_phase if dominant_mass / total >= 0.65 else fallback


def _extract_side_draw_components(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    route: RouteOption,
    product_key: ComponentKey,
    reactant_keys: set[ComponentKey],
    allow_generic_split: bool,
) -> tuple[dict[ComponentKey, float], dict[ComponentKey, float], list[str]]:
    if not state:
        return {}, {}, []
    route_byproduct_names = {normalize_chemical_name(name) for name in route.byproducts}
    side_draw: dict[ComponentKey, float] = {}
    retained: dict[ComponentKey, float] = {}
    notes: list[str] = []
    for key, molar in state.items():
        meta = component_meta[key]
        identifier = normalize_chemical_name(meta.name)
        if key == product_key or key in reactant_keys or molar <= 1e-12:
            _add_component(retained, key, molar)
            continue
        if meta.phase == "gas" or identifier == "water":
            _add_component(retained, key, molar)
            continue
        is_byproduct = identifier in route_byproduct_names or ("byproduct" in meta.name.lower())
        candidate_fraction = 0.0
        if is_byproduct:
            candidate_fraction = 0.92
        elif allow_generic_split and ("acid" in identifier or "glycol" in identifier or "salt" in identifier or "oligomer" in identifier):
            candidate_fraction = 0.55
        if candidate_fraction <= 0.0:
            _add_component(retained, key, molar)
            continue
        draw = molar * candidate_fraction
        _add_component(side_draw, key, draw)
        _add_component(retained, key, molar - draw)
    if side_draw:
        notes.append(
            "Purification section now exposes an explicit side draw for resolved byproduct or heavy-cut components instead of burying them inside the generic waste stream."
        )
    return side_draw, retained, notes


def _build_flowsheet_sections(
    route: RouteOption,
    family: str,
    streams: list[StreamRecord],
    unit_operation_packets: list[UnitOperationPacket],
    recycle_packets: list[RecyclePacket],
    citations: list[str],
    assumptions: list[str],
) -> list[FlowsheetSection]:
    stream_index = {stream.stream_id: stream for stream in streams}
    packet_index = {packet.unit_id: packet for packet in unit_operation_packets}
    sections: list[FlowsheetSection] = []
    for index, blueprint in enumerate(_build_route_section_blueprints(route, family), start=1):
        section_id = blueprint.section_id
        section_type = blueprint.section_type
        label = blueprint.label
        candidate_unit_ids = blueprint.unit_ids
        notes = blueprint.notes
        active_unit_ids = [
            unit_id
            for unit_id in candidate_unit_ids
            if any(stream.source_unit_id == unit_id or stream.destination_unit_id == unit_id for stream in streams)
        ]
        if not active_unit_ids:
            continue
        active_set = set(active_unit_ids)
        inlet_stream_ids = sorted(
            {
                stream.stream_id
                for stream in streams
                if stream.destination_unit_id in active_set and stream.source_unit_id not in active_set
            }
        )
        outlet_stream_ids = sorted(
            {
                stream.stream_id
                for stream in streams
                if stream.source_unit_id in active_set and stream.destination_unit_id not in active_set
            }
        )
        side_draw_stream_ids = sorted(
            {
                stream.stream_id
                for stream in streams
                if stream.source_unit_id in active_set and stream.stream_role == "side_draw"
            }
        )
        section_recycle_loop_ids = sorted(
            {
                packet.loop_id
                for packet in recycle_packets
                if packet.recycle_source_unit_id in active_set
            }
        )
        statuses = [packet_index[unit_id].status for unit_id in active_unit_ids if unit_id in packet_index]
        coverage_warnings = [
            f"Unit `{unit_id}` retains {packet_index[unit_id].coverage_status} packet coverage."
            for unit_id in active_unit_ids
            if unit_id in packet_index and packet_index[unit_id].coverage_status != "complete"
        ]
        status = (
            "blocked"
            if not inlet_stream_ids or not outlet_stream_ids or any(item == "blocked" for item in statuses)
            else "estimated"
            if any(item == "estimated" for item in statuses) or coverage_warnings
            else "converged"
        )
        section_notes = list(notes) + coverage_warnings
        if side_draw_stream_ids:
            section_notes.append(f"Section emits explicit side-draw streams: {', '.join(side_draw_stream_ids)}.")
        if any(stream_index[stream_id].stream_role == "recycle" for stream_id in outlet_stream_ids if stream_id in stream_index):
            section_notes.append("Section contains one or more recycle return streams.")
        sections.append(
            FlowsheetSection(
                section_id=section_id,
                section_type=section_type,
                label=label,
                sequence_index=index,
                unit_ids=active_unit_ids,
                inlet_stream_ids=inlet_stream_ids,
                outlet_stream_ids=outlet_stream_ids,
                side_draw_stream_ids=side_draw_stream_ids,
                recycle_loop_ids=section_recycle_loop_ids,
                status=status,
                notes=section_notes,
                citations=citations,
                assumptions=assumptions,
            )
        )
    return sections


def _unit_metadata(unit_id: str, family: str) -> tuple[str, str]:
    if unit_id == "feed_prep":
        return "feed_preparation", "Feed preparation"
    if unit_id == "reactor":
        return "reactor", "Reaction zone" if family != "solids" else "Carbonation or reaction zone"
    if unit_id == "primary_flash":
        return "flash", "Primary flash and vent recovery"
    if unit_id == "primary_separation":
        return "absorption", "Primary absorption or scrubbing"
    if unit_id == "concentration":
        return ("crystallization", "Crystallization and mother-liquor split") if family == "solids" else ("evaporation", "Water removal and concentration")
    if unit_id == "purification":
        return ("extraction", "Purification train") if family == "extraction" else ("distillation", "Purification train")
    if unit_id == "filtration":
        return "filtration", "Filtration and cake split"
    if unit_id == "drying":
        return "drying", "Drying and finishing"
    if unit_id == "recycle_recovery":
        return "recycle", "Recycle recovery"
    if unit_id == "regeneration":
        return "stripping", "Regeneration and recycle recovery"
    return "unit_operation", unit_id.replace("_", " ").title()


def _packet_status(closure_error_pct: float, *, inlet_count: int, outlet_count: int) -> str:
    if inlet_count == 0 or outlet_count == 0:
        return "blocked"
    if closure_error_pct <= 2.0:
        return "converged"
    if closure_error_pct <= 5.0:
        return "estimated"
    return "blocked"


def _build_unit_operation_packets(
    streams: list[StreamRecord],
    family: str,
    citations: list[str],
    assumptions: list[str],
) -> list[UnitOperationPacket]:
    unit_ids = sorted(
        {
            unit_id
            for stream in streams
            for unit_id in (stream.source_unit_id, stream.destination_unit_id)
            if unit_id and unit_id not in {"battery_limits", "storage", "waste_treatment"}
        }
    )
    packets: list[UnitOperationPacket] = []
    for unit_id in unit_ids:
        unit_type, service = _unit_metadata(unit_id, family)
        inlet_streams = [stream for stream in streams if stream.destination_unit_id == unit_id]
        outlet_streams = [stream for stream in streams if stream.source_unit_id == unit_id]
        if unit_type == "recycle" and (not inlet_streams or not outlet_streams):
            continue
        missing_source_stream_ids = sorted(stream.stream_id for stream in inlet_streams if not stream.source_unit_id)
        missing_destination_stream_ids = sorted(stream.stream_id for stream in outlet_streams if not stream.destination_unit_id)
        inlet_mass = sum(sum(component.mass_flow_kg_hr for component in stream.components) for stream in inlet_streams)
        outlet_mass = sum(sum(component.mass_flow_kg_hr for component in stream.components) for stream in outlet_streams)
        closure_error_pct = 0.0 if max(inlet_mass, outlet_mass, 0.0) <= 0.0 else abs(outlet_mass - inlet_mass) / max(inlet_mass, outlet_mass, 1.0) * 100.0
        notes: list[str] = []
        unresolved_sensitivities: list[str] = []
        if not inlet_streams:
            notes.append("No inlet streams detected for this unit in the solved sequence.")
            unresolved_sensitivities.append("missing inlet stream coverage")
        if not outlet_streams:
            notes.append("No outlet streams detected for this unit in the solved sequence.")
            unresolved_sensitivities.append("missing outlet stream coverage")
        if missing_source_stream_ids:
            notes.append(f"Missing upstream source references on streams: {', '.join(missing_source_stream_ids)}.")
            unresolved_sensitivities.append("missing upstream source references")
        if missing_destination_stream_ids:
            notes.append(f"Missing downstream destination references on streams: {', '.join(missing_destination_stream_ids)}.")
            unresolved_sensitivities.append("missing downstream destination references")
        if any(not stream.phase_hint or stream.phase_hint == "mixed" for stream in inlet_streams + outlet_streams):
            unresolved_sensitivities.append("mixed or unresolved phase basis remains in solved streams")
        if any(not stream.components for stream in inlet_streams + outlet_streams):
            unresolved_sensitivities.append("empty component list on solved stream")
        if closure_error_pct > 2.0:
            notes.append(f"Unit closure is {closure_error_pct:.3f}%, so this unit needs review before detailed design.")
            unresolved_sensitivities.append("material closure above converged range")
        coverage_status = (
            "blocked"
            if not inlet_streams or not outlet_streams or missing_source_stream_ids or missing_destination_stream_ids
            else "partial"
            if unresolved_sensitivities
            else "complete"
        )
        packets.append(
            UnitOperationPacket(
                packet_id=f"{unit_id}_unit_packet",
                unit_id=unit_id,
                unit_type=unit_type,
                service=service,
                inlet_stream_ids=[stream.stream_id for stream in inlet_streams],
                outlet_stream_ids=[stream.stream_id for stream in outlet_streams],
                inlet_mass_flow_kg_hr=round(inlet_mass, 6),
                outlet_mass_flow_kg_hr=round(outlet_mass, 6),
                closure_error_pct=round(closure_error_pct, 6),
                coverage_status=coverage_status,
                missing_source_stream_ids=missing_source_stream_ids,
                missing_destination_stream_ids=missing_destination_stream_ids,
                status=(
                    "blocked"
                    if coverage_status == "blocked"
                    else _packet_status(closure_error_pct, inlet_count=len(inlet_streams), outlet_count=len(outlet_streams))
                ),
                unresolved_sensitivities=sorted(dict.fromkeys(unresolved_sensitivities)),
                notes=notes,
                citations=citations,
                assumptions=assumptions,
            )
        )
    return packets


def _build_recycle_packets(
    streams: list[StreamRecord],
    recycle_solution: dict[str, dict[str, float | int | bool]],
    overall_closure_error_pct: float,
    citations: list[str],
    assumptions: list[str],
) -> list[RecyclePacket]:
    recycle_stream_ids = [
        stream.stream_id
        for stream in streams
        if stream.stream_role == "recycle" and stream.source_unit_id != "battery_limits"
    ]
    purge_stream_ids = [
        stream.stream_id
        for stream in streams
        if stream.stream_role in {"purge", "waste", "vent"} or stream.destination_unit_id == "waste_treatment" or "purge" in stream.description.lower()
    ]
    if not recycle_stream_ids and not purge_stream_ids:
        return []
    component_targets = {name: round(float(result["total_flow"]), 6) for name, result in recycle_solution.items()}
    component_fresh = {name: round(float(result["fresh_flow"]), 6) for name, result in recycle_solution.items()}
    component_recycle = {name: round(float(result["recycle_flow"]), 6) for name, result in recycle_solution.items()}
    component_purge = {name: round(float(result["purge_flow"]), 6) for name, result in recycle_solution.items()}
    actual_recycle = _aggregate_component_molar(streams, recycle_stream_ids)
    actual_purge = _aggregate_component_molar(streams, purge_stream_ids)
    component_errors: dict[str, float] = {}
    component_iterations = {name: int(result["iterations"]) for name, result in recycle_solution.items()}
    for name in recycle_solution:
        recycle_target = component_recycle.get(name, 0.0)
        purge_target = component_purge.get(name, 0.0)
        recycle_error = abs(actual_recycle.get(name, 0.0) - recycle_target) / max(recycle_target, actual_recycle.get(name, 0.0), 1e-9) * 100.0
        target_recovery_ratio = recycle_target / max(recycle_target + purge_target, 1e-9)
        actual_recovery_ratio = actual_recycle.get(name, 0.0) / max(actual_recycle.get(name, 0.0) + actual_purge.get(name, 0.0), 1e-9)
        recovery_ratio_error = abs(actual_recovery_ratio - target_recovery_ratio) * 100.0
        component_errors[name] = round(max(recycle_error, recovery_ratio_error), 6)
    max_iterations = max(int(result["iterations"]) for result in recycle_solution.values()) if recycle_solution else 0
    converged = all(bool(result["converged"]) for result in recycle_solution.values())
    max_component_error = max(component_errors.values(), default=0.0)
    status = (
        "converged"
        if converged and overall_closure_error_pct <= 2.0 and max_component_error <= 2.0
        else "estimated"
        if overall_closure_error_pct <= 5.0 and max_component_error <= 95.0
        else "blocked"
    )
    notes = []
    if not purge_stream_ids:
        notes.append("Recycle loop has no explicit purge stream; verify inert and impurity handling manually.")
    if max_component_error > 10.0:
        notes.append(f"Component recycle/purge error reaches {max_component_error:.3f}% in the current solved loop.")
    return [
        RecyclePacket(
            packet_id="main_recycle_packet",
            loop_id="main_recycle",
            recycle_target_unit_id=next((stream.destination_unit_id for stream in streams if stream.stream_id in recycle_stream_ids), None),
            recycle_stream_ids=recycle_stream_ids,
            purge_stream_ids=purge_stream_ids,
            component_targets_kmol_hr=component_targets,
            component_fresh_kmol_hr=component_fresh,
            component_recycle_kmol_hr=component_recycle,
            component_purge_kmol_hr=component_purge,
            component_convergence_error_pct=component_errors,
            component_iterations=component_iterations,
            convergence_status=status,
            closure_error_pct=round(overall_closure_error_pct, 6),
            max_iterations=max_iterations,
            notes=notes,
            citations=citations,
            assumptions=assumptions,
        )
    ]


def _default_recovery_fractions(route: RouteOption, participant: ReactionParticipant) -> tuple[float, float]:
    text = " ".join(route.separations).lower()
    name = participant.name.lower()
    formula = (participant.formula or "").upper()
    family = _stream_family(route)
    if formula == "H2O" or "water" in name:
        if "distill" in text or "vacuum" in text or route.route_id == "eo_hydration":
            return 0.96, 0.03
        return 0.82, 0.08
    if participant.phase == "gas" or formula in {"CO", "CO2", "SO2", "SO3", "O2", "NH3", "C2H4"}:
        if family == "absorption":
            return 0.72, 0.12
        if family == "solids":
            return 0.01, 0.10
        if family == "distillation":
            return 0.08, 0.15
        return 0.72, 0.12
    if participant.phase == "solid":
        return 0.35, 0.20
    return 0.55, 0.10


def _classify_primary_overhead_fraction(
    key: ComponentKey,
    route: RouteOption,
    component_meta: dict[ComponentKey, ComponentMeta],
    family: str,
    product_key: ComponentKey,
    reactant_keys: set[ComponentKey],
) -> float:
    meta = component_meta[key]
    formula = (meta.formula or "").upper()
    name = meta.name.lower()
    if key == product_key:
        return 0.0 if family != "absorption" else 0.25
    if meta.phase == "solid":
        return 0.0
    if formula in LIGHT_FORMULAS and meta.phase == "gas":
        return 0.94
    if formula in {"CO2", "SO2", "SO3", "NH3"}:
        return 0.88 if family == "absorption" else 0.95
    if formula == "H2O":
        if family in {"distillation", "extraction"}:
            return 0.08
        if family == "solids":
            return 0.02
        return 0.10
    if key in reactant_keys and meta.phase == "gas":
        return 0.75
    if "light" in name or "vent" in name:
        return 0.90
    return 0.04


def _classify_concentration_recycle_fraction(
    key: ComponentKey,
    component_meta: dict[ComponentKey, ComponentMeta],
    family: str,
    reactant_keys: set[ComponentKey],
) -> float:
    meta = component_meta[key]
    formula = (meta.formula or "").upper()
    if formula == "H2O":
        return 0.88 if family in {"distillation", "extraction"} else 0.72
    if key in reactant_keys:
        return 0.42 if family == "solids" else 0.30
    if meta.phase == "gas":
        return 0.55
    return 0.03


def _temperature_basis_c(streams: list[StreamRecord], stream_ids: list[str], fallback: float) -> float:
    values = [stream.temperature_c for stream in streams if stream.stream_id in set(stream_ids)]
    return sum(values) / len(values) if values else fallback


def _pressure_basis_bar(streams: list[StreamRecord], stream_ids: list[str], fallback: float) -> float:
    values = [stream.pressure_bar for stream in streams if stream.stream_id in set(stream_ids)]
    return sum(values) / len(values) if values else fallback


def _select_absorption_solvent_keys(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
) -> list[ComponentKey]:
    ranked = []
    for key, molar in state.items():
        if molar <= 1e-12:
            continue
        identifier = normalize_chemical_name(component_meta[key].name)
        if identifier in {"water", "sulfuric_acid", "spent_acid"}:
            ranked.append((0, key))
        elif component_meta[key].phase != "gas":
            ranked.append((1, key))
    return [item[1] for item in sorted(ranked, key=lambda item: (item[0], component_meta[item[1]].name.lower()))]


def _apply_henry_absorption_split(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    property_packages: PropertyPackageArtifact | None,
    pressure_bar: float,
) -> tuple[dict[ComponentKey, float], list[str]]:
    fractions: dict[ComponentKey, float] = {}
    notes: list[str] = []
    total_gas = sum(
        molar
        for key, molar in state.items()
        if component_meta[key].phase == "gas" or (component_meta[key].formula or "").upper() in {"SO2", "SO3", "CO2", "NH3", "O2"}
    )
    solvent_keys = _select_absorption_solvent_keys(state, component_meta)
    for key, molar in state.items():
        if molar <= 0.0:
            fractions[key] = 0.0
            continue
        if component_meta[key].phase == "solid":
            fractions[key] = 0.0
            continue
        is_gas = component_meta[key].phase == "gas" or (component_meta[key].formula or "").upper() in {"SO2", "SO3", "CO2", "NH3", "O2"}
        default_fraction = 0.88 if is_gas else 0.10
        if not is_gas or not solvent_keys or total_gas <= 1e-12:
            fractions[key] = default_fraction if is_gas else 0.0
            continue
        best_overhead = default_fraction
        best_note = ""
        for solvent_key in solvent_keys:
            partial_pressure = pressure_bar * (molar / max(total_gas, 1e-9))
            retained, model, _, fallback, note = henry_retained_fraction_to_liquid(
                component_meta[key].name,
                component_meta[solvent_key].name,
                molar,
                state.get(solvent_key, 0.0),
                partial_pressure,
                property_packages,
            )
            candidate_overhead = 1.0 - retained if not fallback else default_fraction
            if candidate_overhead < best_overhead:
                best_overhead = candidate_overhead
                best_note = note
            elif fallback and not best_note:
                best_note = note
        fractions[key] = max(min(best_overhead, 1.0), 0.0)
        if best_note:
            notes.append(best_note)
    return fractions, sorted(set(notes))


def _apply_solubility_crystallization_split(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    property_packages: PropertyPackageArtifact | None,
    temperature_c: float,
    product_key: ComponentKey,
) -> tuple[dict[ComponentKey, float], dict[ComponentKey, float], list[str]]:
    mother_liquor: dict[ComponentKey, float] = {}
    crystal_slurry: dict[ComponentKey, float] = {}
    notes: list[str] = []
    solvent_key = next(
        (
            key
            for key in state
            if normalize_chemical_name(component_meta[key].name) == "water"
        ),
        None,
    )
    if product_key not in state or solvent_key is None:
        return {}, dict(state), notes
    product_meta = component_meta[product_key]
    solvent_meta = component_meta[solvent_key]
    solvent_mass = state.get(solvent_key, 0.0) * solvent_meta.molecular_weight_g_mol
    solute_mass = state.get(product_key, 0.0) * product_meta.molecular_weight_g_mol
    limit_kg_per_kg, model, _, fallback, note = solubility_limit_kg_per_kg_solvent(
        product_meta.name,
        solvent_meta.name,
        temperature_c,
        property_packages,
    )
    notes.append(note)
    if fallback or limit_kg_per_kg is None:
        return {}, dict(state), sorted(set(notes))
    dissolved_mass = min(solute_mass, solvent_mass * limit_kg_per_kg)
    precipitated_mass = max(solute_mass - dissolved_mass, 0.0)
    dissolved_molar = dissolved_mass / max(product_meta.molecular_weight_g_mol, 1e-9)
    precipitated_molar = precipitated_mass / max(product_meta.molecular_weight_g_mol, 1e-9)
    for key, molar in state.items():
        if key == product_key:
            _add_component(mother_liquor, key, dissolved_molar)
            _add_component(crystal_slurry, key, precipitated_molar)
            continue
        if key == solvent_key:
            entrained = molar * 0.08
            _add_component(crystal_slurry, key, entrained)
            _add_component(mother_liquor, key, molar - entrained)
            continue
        if component_meta[key].phase == "solid":
            _add_component(crystal_slurry, key, molar)
        else:
            _add_component(mother_liquor, key, molar)
    notes.append(
        f"SLE basis '{model}' dissolved {dissolved_mass:.2f} kg/h of {product_meta.name} in {solvent_meta.name} and precipitated {precipitated_mass:.2f} kg/h."
    )
    return mother_liquor, crystal_slurry, sorted(set(notes))


def _distribute_purification_outputs(
    state: dict[ComponentKey, float],
    component_meta: dict[ComponentKey, ComponentMeta],
    product_key: ComponentKey,
    reactant_keys: set[ComponentKey],
    family: str,
    recycle_targets: dict[ComponentKey, float] | None = None,
) -> tuple[dict[ComponentKey, float], dict[ComponentKey, float], dict[ComponentKey, float]]:
    recycle_state: dict[ComponentKey, float] = {}
    product_state: dict[ComponentKey, float] = {}
    waste_state: dict[ComponentKey, float] = {}
    for key, molar in state.items():
        meta = component_meta[key]
        formula = (meta.formula or "").upper()
        if key == product_key:
            recovery = 0.997 if family == "distillation" else 0.994 if family in {"extraction", "absorption"} else 0.989
            _add_component(product_state, key, molar * recovery)
            _add_component(waste_state, key, molar * (1.0 - recovery))
            continue
        if key in reactant_keys or formula in {"H2O", "NH3"}:
            requested = (recycle_targets or {}).get(key, 0.0)
            recycle_flow = min(requested, molar)
            _add_component(recycle_state, key, recycle_flow)
            _add_component(waste_state, key, molar - recycle_flow)
            continue
        if meta.phase == "gas" or formula in {"CO2", "SO2", "SO3"}:
            _add_component(recycle_state, key, molar * 0.35)
            _add_component(waste_state, key, molar * 0.65)
            continue
        _add_component(waste_state, key, molar)
    return recycle_state, product_state, waste_state


def build_generic_sequence_streams(
    product_mass_kg_hr: float,
    route: RouteOption,
    reaction_system: ReactionSystem,
    citations: list[str],
    assumptions: list[str],
    property_packages: PropertyPackageArtifact | None = None,
) -> SequenceSolveResult:
    family = _stream_family(route)
    section_blueprints = _build_route_section_blueprints(route, family)
    section_lookup = _blueprint_by_unit(section_blueprints)
    participants = route.participants
    reactants = [item for item in participants if item.role == "reactant"]
    products = [item for item in participants if item.role == "product"]
    if not products:
        raise ValueError(f"Route '{route.route_id}' has no product participant.")
    product = products[0]
    product_key = _participant_key(product)
    component_meta: dict[ComponentKey, ComponentMeta] = {
        _participant_key(item): ComponentMeta(
            name=item.name,
            formula=item.formula,
            molecular_weight_g_mol=item.molecular_weight_g_mol,
            phase=item.phase or "",
        )
        for item in participants
    }

    product_kmol_hr = product_mass_kg_hr / max(product.molecular_weight_g_mol, 1e-9)
    main_extent = product_kmol_hr / max(product.coefficient, 1e-9)
    reacted_extent = main_extent / max(reaction_system.selectivity_fraction, 1e-9)
    feed_extent = reacted_extent / max(reaction_system.conversion_fraction, 1e-9)
    byproduct_extent = max(reacted_extent - main_extent, 0.0)

    target_total_by_reactant: dict[str, float] = {}
    consumed_by_reactant: dict[str, float] = {}
    recovery_by_reactant: dict[str, float] = {}
    purge_by_reactant: dict[str, float] = {}
    reactant_keys = {_participant_key(item) for item in reactants}
    recycle_candidate_key = next(
        (
            _participant_key(item)
            for item in reactants
            if (item.formula or "").upper() == "H2O" or "water" in item.name.lower()
        ),
        _participant_key(reactants[0]) if reactants else None,
    )

    for reactant in reactants:
        key = reactant.name
        total_feed_kmol_hr = feed_extent * reactant.coefficient
        if recycle_candidate_key == _participant_key(reactant) and reaction_system.excess_ratio > 1.0:
            total_feed_kmol_hr *= reaction_system.excess_ratio
        target_total_by_reactant[key] = total_feed_kmol_hr
        consumed_by_reactant[key] = reacted_extent * reactant.coefficient
        recovery, purge = _default_recovery_fractions(route, reactant)
        recovery_by_reactant[key] = recovery
        purge_by_reactant[key] = purge

    recycle_solution = solve_multi_component_recycle_loop(
        target_total_by_reactant,
        consumed_by_reactant,
        recovery_by_reactant,
        purge_by_reactant,
    )

    fresh_state: dict[ComponentKey, float] = {}
    recycle_state: dict[ComponentKey, float] = {}
    purge_state: dict[ComponentKey, float] = {}
    feed_state: dict[ComponentKey, float] = {}
    feed_breakdown: list[tuple[ReactionParticipant, float, float, float]] = []
    streams: list[StreamRecord] = []
    total_fresh_feed_mass = 0.0

    for index, reactant in enumerate(reactants, start=1):
        key = _participant_key(reactant)
        solution = recycle_solution[reactant.name]
        fresh_kmol_hr = float(solution["fresh_flow"])
        recycle_kmol_hr = float(solution["recycle_flow"])
        purge_kmol_hr = float(solution["purge_flow"])
        total_kmol_hr = float(solution["total_flow"])
        _add_component(fresh_state, key, fresh_kmol_hr)
        _add_component(recycle_state, key, recycle_kmol_hr)
        _add_component(purge_state, key, purge_kmol_hr)
        _add_component(feed_state, key, total_kmol_hr)
        feed_breakdown.append((reactant, fresh_kmol_hr, recycle_kmol_hr, total_kmol_hr))
        fresh_mass = fresh_kmol_hr * reactant.molecular_weight_g_mol
        total_fresh_feed_mass += fresh_mass
        streams.append(
            _stream(
                stream_id=f"S-10{index}",
                description=f"{reactant.name} fresh feed",
                temperature_c=25.0,
                pressure_bar=max(route.operating_pressure_bar, 1.0),
                state={key: fresh_kmol_hr},
                component_meta=component_meta,
                source_unit_id="battery_limits",
                destination_unit_id="feed_prep",
                phase_hint=reactant.phase or "mixed",
                stream_role="feed",
                section_id=_section_id_for_unit(section_blueprints, "feed_prep", "feed_handling"),
            )
        )

    streams.append(
        _stream(
            stream_id="S-150",
            description="Mixed reactor feed",
            temperature_c=max(route.operating_temperature_c - 15.0, 30.0),
            pressure_bar=max(route.operating_pressure_bar, 1.0),
            state=feed_state,
            component_meta=component_meta,
            source_unit_id="feed_prep",
            destination_unit_id="reactor",
            phase_hint=_infer_phase_hint(feed_state, component_meta, "mixed"),
            stream_role="intermediate",
            section_id=_section_id_for_unit(section_blueprints, "reactor", "reaction"),
        )
    )

    reactor_state = dict(feed_state)
    consumed_reactant_mass_kg_hr = 0.0
    for reactant in reactants:
        consumed_reactant_mass_kg_hr += reacted_extent * reactant.coefficient * reactant.molecular_weight_g_mol
        _add_component(reactor_state, _participant_key(reactant), -(reacted_extent * reactant.coefficient))
    _add_component(reactor_state, product_key, product_kmol_hr)
    byproduct_estimates = reaction_system.byproduct_closure.estimates if reaction_system.byproduct_closure else []
    residual_byproduct_mass_kg_hr = max(consumed_reactant_mass_kg_hr - (product_kmol_hr * product.molecular_weight_g_mol), 0.0)
    if byproduct_extent > 0.0 and byproduct_estimates:
        allocation_total = sum(max(item.allocation_fraction, 0.0) for item in byproduct_estimates) or 1.0
        for estimate in byproduct_estimates:
            if residual_byproduct_mass_kg_hr <= 0.0:
                break
            _add_byproduct_estimate(
                reactor_state,
                component_meta,
                estimate,
                residual_byproduct_mass_kg_hr * (max(estimate.allocation_fraction, 0.0) / allocation_total),
            )
    if byproduct_extent > 0.0 and not byproduct_estimates:
        pseudo_key = _component_key("Heavy ends", None)
        pseudo_mw = max(product.molecular_weight_g_mol * 1.1, 1.0)
        component_meta[pseudo_key] = ComponentMeta(
            name="Heavy ends",
            formula=None,
            molecular_weight_g_mol=pseudo_mw,
            phase="liquid",
        )
        _add_component(reactor_state, pseudo_key, residual_byproduct_mass_kg_hr / pseudo_mw)

    streams.append(
        _stream(
            stream_id="S-201",
            description="Reactor effluent",
            temperature_c=route.operating_temperature_c,
            pressure_bar=max(route.operating_pressure_bar, 1.0),
            state=reactor_state,
            component_meta=component_meta,
            source_unit_id="reactor",
            destination_unit_id=(
                "primary_separation"
                if family == "absorption"
                else "primary_flash"
                if "primary_flash" in section_lookup
                else (_downstream_unit_after(section_blueprints, "reactor") or "purification")
            ),
            phase_hint=_infer_phase_hint(reactor_state, component_meta, "mixed"),
            stream_role="intermediate",
            section_id=_section_id_for_unit(section_blueprints, "reactor", "reaction"),
        )
    )

    primary_split_fractions = {
        key: _classify_primary_overhead_fraction(key, route, component_meta, family, product_key, reactant_keys)
        for key in reactor_state
    }
    if family == "absorption":
        absorption_split, absorption_notes = _apply_henry_absorption_split(
            reactor_state,
            component_meta,
            property_packages,
            max(route.operating_pressure_bar - 0.8, 1.0),
        )
        primary_split_fractions.update(absorption_split)
        assumptions = assumptions + absorption_notes if absorption_notes else assumptions
    primary_overhead, primary_bottoms = _split_state(reactor_state, primary_split_fractions)
    primary_unit_id = "primary_separation" if family == "absorption" else "primary_flash"
    primary_bottom_destination = _downstream_unit_after(section_blueprints, primary_unit_id) or (
        "regeneration" if family == "absorption" else "purification"
    )
    streams.append(
        _stream(
            stream_id="S-202",
            description="Primary separation overhead / vent / purge",
            temperature_c=max(route.operating_temperature_c - 35.0, 35.0),
            pressure_bar=max(route.operating_pressure_bar - 1.5, 1.0),
            state=primary_overhead,
            component_meta=component_meta,
            source_unit_id="primary_flash" if family != "absorption" else "primary_separation",
            destination_unit_id="waste_treatment",
            phase_hint=_infer_phase_hint(primary_overhead, component_meta, "gas"),
            stream_role="vent" if family != "solids" else "waste",
            section_id=_section_id_for_unit(section_blueprints, primary_unit_id, "primary_absorption" if family == "absorption" else "primary_recovery"),
        )
    )
    streams.append(
        _stream(
            stream_id="S-203",
            description="Primary separation bottoms / rich liquid",
            temperature_c=max(route.operating_temperature_c - 10.0, 45.0),
            pressure_bar=max(route.operating_pressure_bar - 0.8, 1.0),
            state=primary_bottoms,
            component_meta=component_meta,
            source_unit_id="primary_flash" if family != "absorption" else "primary_separation",
            destination_unit_id=primary_bottom_destination,
            phase_hint=_infer_phase_hint(primary_bottoms, component_meta, "liquid" if family != "solids" else "slurry"),
            stream_role="intermediate",
            section_id=_section_id_for_unit(section_blueprints, primary_unit_id, "primary_absorption" if family == "absorption" else "primary_recovery"),
        )
    )

    if family in {"distillation", "extraction", "solids"}:
        concentration_split: dict[ComponentKey, float] = {}
        concentration_recycle_targets: dict[ComponentKey, float] = {}
        if family == "solids":
            concentration_recycle, purification_feed, sle_notes = _apply_solubility_crystallization_split(
                primary_bottoms,
                component_meta,
                property_packages,
                35.0,
                product_key,
            )
            if not concentration_recycle and purification_feed == primary_bottoms:
                for key, molar in primary_bottoms.items():
                    if molar <= 0.0:
                        concentration_split[key] = 0.0
                        continue
                    default_fraction = _classify_concentration_recycle_fraction(key, component_meta, family, reactant_keys)
                    if key == product_key or component_meta[key].phase == "solid":
                        concentration_split[key] = 0.0
                        continue
                    target_recycle = recycle_state.get(key, 0.0)
                    target_fraction = min(target_recycle / molar, 1.0) if target_recycle > 0.0 else default_fraction
                    concentration_split[key] = min(default_fraction, target_fraction)
                    concentration_recycle_targets[key] = molar * concentration_split[key]
                concentration_recycle, purification_feed = _split_state(primary_bottoms, concentration_split)
            assumptions = assumptions + sle_notes if sle_notes else assumptions
        else:
            for key, molar in primary_bottoms.items():
                if molar <= 0.0:
                    concentration_split[key] = 0.0
                    continue
                default_fraction = _classify_concentration_recycle_fraction(key, component_meta, family, reactant_keys)
                if key == product_key or component_meta[key].phase == "solid":
                    concentration_split[key] = 0.0
                    continue
                target_recycle = recycle_state.get(key, 0.0)
                target_fraction = min(target_recycle / molar, 1.0) if target_recycle > 0.0 else default_fraction
                concentration_split[key] = min(default_fraction, target_fraction)
                concentration_recycle_targets[key] = molar * concentration_split[key]
            concentration_recycle, purification_feed = _split_state(primary_bottoms, concentration_split)
        streams.append(
            _stream(
                stream_id="S-301",
                description="Recovered condensate / mother liquor recycle",
                temperature_c=95.0 if family == "distillation" else 55.0,
                pressure_bar=1.1,
                state=concentration_recycle,
                component_meta=component_meta,
                source_unit_id="concentration",
                destination_unit_id=_recycle_target_for(section_blueprints, "concentration"),
                phase_hint=_infer_phase_hint(concentration_recycle, component_meta, "vapor" if family == "distillation" else "liquid"),
                stream_role="recycle",
                section_id=_section_id_for_unit(section_blueprints, "concentration", "concentration"),
            )
        )
        streams.append(
            _stream(
                stream_id="S-302",
                description="Concentrated stream to purification",
                temperature_c=125.0 if family == "distillation" else 45.0,
                pressure_bar=1.05,
                state=purification_feed,
                component_meta=component_meta,
                source_unit_id="concentration",
                destination_unit_id=_downstream_unit_after(section_blueprints, "concentration") or ("purification" if family != "solids" else "filtration"),
                phase_hint=_infer_phase_hint(purification_feed, component_meta, "liquid" if family != "solids" else "slurry"),
                stream_role="intermediate",
                section_id=_section_id_for_unit(section_blueprints, "concentration", "concentration"),
            )
        )
        remaining_recycle_targets = {
            key: max(recycle_state.get(key, 0.0) - concentration_recycle.get(key, 0.0), 0.0)
            for key in recycle_state
        }
    elif family == "absorption":
        regeneration_split = {
            key: 0.78 if key in reactant_keys or (component_meta[key].formula or "").upper() in {"H2O", "SO2"} else 0.0
            for key in primary_bottoms
        }
        regeneration_adjustments, regeneration_notes = _apply_henry_absorption_split(
            primary_bottoms,
            component_meta,
            property_packages,
            1.2,
        )
        for key, overhead_fraction in regeneration_adjustments.items():
            is_gas = component_meta[key].phase == "gas" or (component_meta[key].formula or "").upper() in {"SO2", "SO3", "CO2", "NH3", "O2"}
            if is_gas:
                regeneration_split[key] = max(regeneration_split.get(key, 0.0), overhead_fraction)
        assumptions = assumptions + regeneration_notes if regeneration_notes else assumptions
        regeneration_recycle, product_hold = _split_state(primary_bottoms, regeneration_split)
        streams.append(
            _stream(
                stream_id="S-301",
                description="Regenerated recycle stream",
                temperature_c=70.0,
                pressure_bar=1.2,
                state=regeneration_recycle,
                component_meta=component_meta,
                source_unit_id="regeneration",
                destination_unit_id=_recycle_target_for(section_blueprints, "regeneration"),
                phase_hint=_infer_phase_hint(regeneration_recycle, component_meta, "gas"),
                stream_role="recycle",
                section_id=_section_id_for_unit(section_blueprints, "regeneration", "regeneration"),
            )
        )
        product_state: dict[ComponentKey, float] = {}
        absorption_waste_state = {}
        if product_hold:
            _add_component(product_state, product_key, product_hold.get(product_key, 0.0))
            for key, molar in product_hold.items():
                if key == product_key:
                    continue
                formula = (component_meta[key].formula or "").upper()
                if formula == "H2O":
                    retained_water = molar * 0.15
                    _add_component(product_state, key, retained_water)
                    _add_component(absorption_waste_state, key, molar - retained_water)
                    continue
                _add_component(absorption_waste_state, key, molar)
        else:
            _add_component(product_state, product_key, reactor_state.get(product_key, 0.0))
        streams.append(
            _stream(
                stream_id="S-401",
                description="Product acid stream",
                temperature_c=45.0,
                pressure_bar=1.1,
                state=product_state,
                component_meta=component_meta,
                source_unit_id="regeneration",
                destination_unit_id="storage",
                phase_hint=_infer_phase_hint(product_state, component_meta, "liquid"),
                stream_role="product",
                section_id=_section_id_for_unit(section_blueprints, "regeneration", "regeneration"),
            )
        )
        if absorption_waste_state:
            streams.append(
                _stream(
                    stream_id="S-402",
                    description="Weak acid bleed / off-spec regeneration purge",
                    temperature_c=40.0,
                    pressure_bar=1.0,
                    state=absorption_waste_state,
                    component_meta=component_meta,
                    source_unit_id="regeneration",
                    destination_unit_id="waste_treatment",
                    phase_hint=_infer_phase_hint(absorption_waste_state, component_meta, "mixed"),
                    stream_role="waste",
                    section_id=_section_id_for_unit(section_blueprints, "regeneration", "regeneration"),
                )
            )
        purification_recycle: dict[ComponentKey, float] = {}
        waste_state = absorption_waste_state
        remaining_recycle_targets = {}
    else:
        recycle_recovery_target = _recycle_target_for(section_blueprints, "recycle_recovery")
        recycle_recovery_feed = (
            primary_bottoms if primary_bottom_destination == "recycle_recovery" else {}
        )
        recycle_recovery_stream = (
            _merge_states(recycle_state, recycle_recovery_feed)
            if recycle_recovery_target == "purification"
            else dict(recycle_state)
        )
        if recycle_recovery_stream:
            streams.append(
                _stream(
                    stream_id="S-301",
                    description=(
                        "Cleanup / recycle recovery stream"
                        if recycle_recovery_feed
                        else "Recovered recycle stream"
                    ),
                    temperature_c=max(route.operating_temperature_c - 25.0, 30.0),
                    pressure_bar=max(route.operating_pressure_bar - 1.0, 1.0),
                    state=recycle_recovery_stream,
                    component_meta=component_meta,
                    source_unit_id="recycle_recovery",
                    destination_unit_id=recycle_recovery_target,
                    phase_hint=_infer_phase_hint(recycle_recovery_stream, component_meta, "mixed"),
                    stream_role="recycle",
                    section_id=_section_id_for_unit(section_blueprints, "recycle_recovery", "purification"),
                )
            )
        if recycle_recovery_target == "purification":
            purification_feed = (
                recycle_recovery_stream
                if recycle_recovery_feed
                else _merge_states(primary_bottoms, recycle_state)
            )
            remaining_recycle_targets = dict(recycle_state)
        else:
            purification_feed = primary_bottoms
            remaining_recycle_targets = {}

    if family != "absorption":
        purification_recycle, product_state, waste_state = _distribute_purification_outputs(
            purification_feed,
            component_meta,
            product_key,
            reactant_keys,
            family,
            recycle_targets=remaining_recycle_targets,
        )
        for key, target in remaining_recycle_targets.items():
            unmet = max(target - purification_recycle.get(key, 0.0), 0.0)
            if unmet <= 1e-10:
                continue
            shift = min(unmet, waste_state.get(key, 0.0))
            if shift <= 1e-10:
                continue
            _add_component(purification_recycle, key, shift)
            _add_component(waste_state, key, -shift)
        if purification_recycle and family != "solids":
            streams.append(
                _stream(
                    stream_id="S-401",
                    description="Light ends / recoverable recycle",
                    temperature_c=45.0,
                    pressure_bar=1.0,
                    state=purification_recycle,
                    component_meta=component_meta,
                    source_unit_id="purification" if family != "solids" else "filtration",
                    destination_unit_id=_recycle_target_for(section_blueprints, "purification"),
                    phase_hint=_infer_phase_hint(purification_recycle, component_meta, "mixed"),
                    stream_role="recycle",
                    section_id=_section_id_for_unit(section_blueprints, "purification", "purification"),
                )
            )
        if family == "solids":
            if purification_recycle:
                streams.append(
                    _stream(
                        stream_id="S-351",
                        description="Filtrate recycle / mother liquor recovery",
                        temperature_c=35.0,
                        pressure_bar=1.02,
                        state=purification_recycle,
                        component_meta=component_meta,
                        source_unit_id="filtration",
                        destination_unit_id=_recycle_target_for(section_blueprints, "filtration"),
                        phase_hint=_infer_phase_hint(purification_recycle, component_meta, "liquid"),
                        stream_role="recycle",
                        section_id=_section_id_for_unit(section_blueprints, "filtration", "solids_finishing"),
                    )
                )
            wet_cake_state: dict[ComponentKey, float] = {}
            dry_product_state: dict[ComponentKey, float] = {}
            for key, molar in product_state.items():
                moisture_fraction = 1.0 if (component_meta[key].formula or "").upper() == "H2O" else 0.0
                if key == product_key:
                    _add_component(wet_cake_state, key, molar)
                    _add_component(dry_product_state, key, molar)
                elif moisture_fraction > 0.0:
                    retained_moisture = molar * 0.12
                    _add_component(wet_cake_state, key, retained_moisture)
                else:
                    _add_component(waste_state, key, molar)
            streams.append(
                _stream(
                    stream_id="S-401",
                    description="Wet cake to drying",
                    temperature_c=35.0,
                    pressure_bar=1.05,
                    state=wet_cake_state,
                    component_meta=component_meta,
                    source_unit_id="filtration",
                    destination_unit_id=_downstream_unit_after(section_blueprints, "filtration") or "storage",
                    phase_hint=_infer_phase_hint(wet_cake_state, component_meta, "solid"),
                    stream_role="intermediate",
                    section_id=_section_id_for_unit(section_blueprints, "filtration", "solids_finishing"),
                )
            )
            streams.append(
                _stream(
                    stream_id="S-402",
                    description="On-spec product",
                    temperature_c=35.0,
                    pressure_bar=1.1,
                    state=dry_product_state,
                    component_meta=component_meta,
                    source_unit_id="drying",
                    destination_unit_id="storage",
                    phase_hint=_infer_phase_hint(dry_product_state, component_meta, "solid"),
                    stream_role="product",
                    section_id=_section_id_for_unit(section_blueprints, "drying", "solids_finishing"),
                )
            )
        else:
            side_draw_state: dict[ComponentKey, float] = {}
            if family in {"distillation", "extraction", "generic"} and _allow_side_draw(section_blueprints, "purification"):
                side_draw_state, waste_state, side_draw_notes = _extract_side_draw_components(
                    waste_state,
                    component_meta,
                    route,
                    product_key,
                    reactant_keys,
                    allow_generic_split=True,
                )
                assumptions = assumptions + side_draw_notes if side_draw_notes else assumptions
                if side_draw_state:
                    streams.append(
                        _stream(
                            stream_id="S-404",
                            description="Purification side draw / coproduct cut",
                            temperature_c=50.0,
                            pressure_bar=1.08,
                            state=side_draw_state,
                            component_meta=component_meta,
                            source_unit_id="purification",
                            destination_unit_id="battery_limits",
                            phase_hint=_infer_phase_hint(side_draw_state, component_meta, "liquid"),
                            stream_role="side_draw",
                            section_id=_section_id_for_unit(section_blueprints, "purification", "purification"),
                        )
                    )
            streams.append(
                _stream(
                    stream_id="S-402",
                    description="On-spec product",
                    temperature_c=45.0,
                    pressure_bar=1.1,
                    state=product_state,
                    component_meta=component_meta,
                    source_unit_id="purification",
                    destination_unit_id="storage",
                    phase_hint=_infer_phase_hint(product_state, component_meta, "liquid"),
                    stream_role="product",
                    section_id=_section_id_for_unit(section_blueprints, "purification", "purification"),
                )
            )
        combined_waste = dict(waste_state)
        streams.append(
            _stream(
                stream_id="S-403",
                description="Waste / purge / heavy ends",
                temperature_c=55.0,
                pressure_bar=1.05,
                state=combined_waste,
                component_meta=component_meta,
                source_unit_id="purification" if family != "solids" else "filtration",
                destination_unit_id="waste_treatment",
                phase_hint=_infer_phase_hint(combined_waste, component_meta, "mixed"),
                stream_role="waste",
                section_id=_section_id_for_unit(section_blueprints, "filtration" if family == "solids" else "purification", "solids_finishing" if family == "solids" else "purification"),
            )
        )
        waste_state = combined_waste

    packet_streams = deepcopy(streams)
    unit_operation_packets = _build_unit_operation_packets(packet_streams, family, citations, assumptions)
    phase_split_specs, separator_performances, separation_packets = build_separator_models(
        packet_streams,
        family,
        unit_operation_packets,
        citations,
        assumptions,
        property_packages=property_packages,
    )
    recycle_packets, convergence_summaries = build_recycle_network_packets(
        packet_streams,
        recycle_solution,
        0.0,
        citations,
        assumptions,
    )
    sections = _build_flowsheet_sections(
        route,
        family,
        packet_streams,
        unit_operation_packets,
        recycle_packets,
        citations,
        assumptions,
    )

    total_external_out = _reconcile_external_closure(streams, component_meta, total_fresh_feed_mass, product_key)
    closure_error_pct = 0.0
    if total_fresh_feed_mass > 0.0:
        closure_error_pct = abs(total_fresh_feed_mass - total_external_out) / total_fresh_feed_mass * 100.0
    for packet in recycle_packets:
        packet.closure_error_pct = round(closure_error_pct, 6)
        if packet.convergence_status == "converged" and closure_error_pct > 2.0:
            packet.convergence_status = "estimated"
            packet.notes.append("Overall external closure remains above the converged range after reconciliation.")
        elif packet.convergence_status != "blocked" and closure_error_pct > 5.0:
            packet.convergence_status = "blocked"
            packet.notes.append("Overall external closure is too high after reconciliation.")
    for summary in convergence_summaries:
        if summary.convergence_status == "converged" and closure_error_pct > 2.0:
            summary.convergence_status = "estimated"
            summary.notes.append("Overall external closure remains above the converged range after reconciliation.")
        elif summary.convergence_status != "blocked" and closure_error_pct > 5.0:
            summary.convergence_status = "blocked"
            summary.notes.append("Overall external closure is too high after reconciliation.")

    traces = [
        CalcTrace(
            trace_id="sequence_main_extent",
            title="Main reaction extent",
            formula="extent = product_kmol / nu_product",
            substitutions={"product_kmol": f"{product_kmol_hr:.6f}", "nu_product": f"{product.coefficient:.3f}"},
            result=f"{main_extent:.6f}",
            units="kmol/h",
        ),
        CalcTrace(
            trace_id="sequence_feed_extent",
            title="Feed extent with conversion/selectivity",
            formula="feed_extent = (product_kmol / nu_product) / (selectivity * conversion)",
            substitutions={
                "selectivity": f"{reaction_system.selectivity_fraction:.4f}",
                "conversion": f"{reaction_system.conversion_fraction:.4f}",
            },
            result=f"{feed_extent:.6f}",
            units="kmol/h",
        ),
        CalcTrace(
            trace_id="sequence_byproduct_closure",
            title="Byproduct closure allocation",
            formula="Residual byproduct mass is allocated across explicit byproduct-closure estimates",
            substitutions={
                "closure_status": reaction_system.byproduct_closure.closure_status if reaction_system.byproduct_closure else "fallback",
                "estimate_count": str(len(byproduct_estimates)),
                "residual_mass_kg_hr": f"{residual_byproduct_mass_kg_hr:.3f}",
            },
            result=f"{len(byproduct_estimates)} estimates",
            units="items",
            notes="This replaces the older implicit heavy-ends fallback whenever the reaction system carries a byproduct-closure artifact.",
        ),
        CalcTrace(
            trace_id="sequence_recycle_components",
            title="Multi-component recycle solution",
            formula="Solve recycle per reactant using target_total, consumed, recovery, and purge fractions",
            substitutions={item[0].name: f"fresh={item[1]:.3f}; recycle={item[2]:.3f}; total={item[3]:.3f}" for item in feed_breakdown},
            result=f"{len(feed_breakdown)} components solved",
            units="components",
            notes="This is the first generic convergence slice: reactants are solved through the same recycle/purge loop instead of family-specific inline math.",
        ),
        CalcTrace(
            trace_id="sequence_stage_count",
            title="Unit-sequence expansion",
            formula="stream_count = feeds + mixed feed + reactor + separation + recycle + product/waste",
            substitutions={"family": family},
            result=f"{len(streams)}",
            units="streams",
        ),
        CalcTrace(
            trace_id="sequence_closure",
            title="Fresh-feed to external-out closure",
            formula="closure = |fresh_feed - external_out| / fresh_feed",
            substitutions={"fresh_feed": f"{total_fresh_feed_mass:.3f}", "external_out": f"{total_external_out:.3f}"},
            result=f"{closure_error_pct:.6f}",
            units="%",
        ),
    ]
    stage_labels = [section.section_id for section in sections]
    return SequenceSolveResult(
        streams=streams,
        total_fresh_feed_mass_kg_hr=round(total_fresh_feed_mass, 6),
        total_external_out_mass_kg_hr=round(total_external_out, 6),
        closure_error_pct=round(closure_error_pct, 6),
        calc_traces=traces,
        sequence_family=family,
        stage_labels=stage_labels,
        unit_operation_packets=unit_operation_packets,
        phase_split_specs=phase_split_specs,
        separator_performances=separator_performances,
        separation_packets=separation_packets,
        recycle_packets=recycle_packets,
        convergence_summaries=convergence_summaries,
        sections=sections,
    )
