from __future__ import annotations

from dataclasses import dataclass, field
import math

from aoc.models import (
    EnergyBalance,
    HeatCompositeInterval,
    HeatExchangerTrainStep,
    HeatMatch,
    HeatMatchCandidate,
    HeatNetworkArchitecture,
    HeatNetworkCase,
    HeatStream,
    HeatStreamSet,
    HeatUtilityIsland,
    UtilityTrainPackageItem,
    UtilityArchitectureDecision,
    UtilityNetworkDecision,
)


@dataclass
class _IslandEnvelope:
    island_id: str
    topology: str
    hot_stream_ids: list[str]
    cold_stream_ids: list[str]
    unit_ids: list[str]
    architecture_role: str = "generic"
    header_level: int = 0
    cluster_id: str | None = None
    case_matches: list[HeatMatch] = field(default_factory=list)
    packet_candidates: list[HeatMatchCandidate] = field(default_factory=list)
    recoverable_potential_kw: float = 0.0
    target_recovered_duty_kw: float = 0.0
    selection_priority: float = 0.0
    cross_service: bool = False


def _topology_label(case_id: str, title: str) -> str:
    lowered = f"{case_id} {title}".lower()
    if "shared_htm" in lowered or "shared htm" in lowered:
        return "shared HTM island network"
    if "cluster" in lowered and ("reboiler" in lowered or "condenser" in lowered):
        return "condenser-reboiler cluster"
    if "header" in lowered:
        return "staged utility header network"
    if "htm" in lowered or "dowtherm" in lowered:
        return "reactor-to-reboiler HTM loop"
    if "multi" in lowered:
        return "multi-effect recovery network"
    if "direct" in lowered or "feed" in lowered:
        return "direct heat-match network"
    if "no_recovery" in lowered or "no recovery" in lowered:
        return "utility-only architecture"
    return "hybrid recovery network"


def _packet_heat_streams(energy_balance: EnergyBalance | None) -> list[HeatStream]:
    if energy_balance is None:
        return []
    streams: list[HeatStream] = []
    for packet in energy_balance.unit_thermal_packets:
        if packet.cooling_kw > 0.0:
            streams.append(
                HeatStream(
                    stream_id=f"{packet.packet_id}_hot",
                    name=f"{packet.unit_id} hot-side packet",
                    kind="hot",
                    source_unit_id=packet.unit_id,
                    supply_temp_c=packet.hot_supply_temp_c,
                    target_temp_c=packet.hot_target_temp_c,
                    duty_kw=packet.cooling_kw,
                    phase_change=packet.duty_type == "latent",
                    notes="Derived from solved unit thermal packet.",
                    citations=packet.citations,
                    assumptions=packet.assumptions,
                )
            )
        if packet.heating_kw > 0.0:
            streams.append(
                HeatStream(
                    stream_id=f"{packet.packet_id}_cold",
                    name=f"{packet.unit_id} cold-side packet",
                    kind="cold",
                    source_unit_id=packet.unit_id,
                    supply_temp_c=packet.cold_supply_temp_c,
                    target_temp_c=packet.cold_target_temp_c,
                    duty_kw=packet.heating_kw,
                    phase_change=packet.duty_type == "latent",
                    notes="Derived from solved unit thermal packet.",
                    citations=packet.citations,
                    assumptions=packet.assumptions,
                )
            )
    return streams


def _packet_match_candidates(energy_balance: EnergyBalance | None) -> list[HeatMatchCandidate]:
    if energy_balance is None:
        return []
    return [
        HeatMatchCandidate(
            candidate_id=candidate.candidate_id,
            hot_stream_id=f"{candidate.hot_packet_id}_hot",
            cold_stream_id=f"{candidate.cold_packet_id}_cold",
            topology="direct heat-match network" if candidate.topology == "direct" else "reactor-to-reboiler HTM loop",
            recovered_duty_kw=candidate.recovered_duty_kw,
            feasible=candidate.feasible,
            notes=f"{candidate.notes} Minimum approach {candidate.minimum_approach_temp_c:.1f} C.",
            citations=candidate.citations,
            assumptions=candidate.assumptions,
        )
        for candidate in energy_balance.network_candidates
    ]


def _build_composite_intervals(
    streams: list[HeatStream],
    min_approach_temp_c: float,
) -> list[HeatCompositeInterval]:
    if not streams:
        return []
    hot_shift = min_approach_temp_c / 2.0
    cold_shift = min_approach_temp_c / 2.0
    shifted_temps = sorted(
        {
            round(
                temp - hot_shift if stream.kind == "hot" else temp + cold_shift,
                6,
            )
            for stream in streams
            for temp in (stream.supply_temp_c, stream.target_temp_c)
        },
        reverse=True,
    )
    if len(shifted_temps) < 2:
        return []

    def interval_duty(stream: HeatStream, upper: float, lower: float) -> float:
        shifted_supply = stream.supply_temp_c - hot_shift if stream.kind == "hot" else stream.supply_temp_c + cold_shift
        shifted_target = stream.target_temp_c - hot_shift if stream.kind == "hot" else stream.target_temp_c + cold_shift
        span = max(abs(shifted_supply - shifted_target), 1e-9)
        interval_upper = min(max(shifted_supply, shifted_target), upper)
        interval_lower = max(min(shifted_supply, shifted_target), lower)
        if interval_upper <= interval_lower:
            return 0.0
        return stream.duty_kw * ((interval_upper - interval_lower) / span)

    intervals: list[HeatCompositeInterval] = []
    for index, (upper, lower) in enumerate(zip(shifted_temps, shifted_temps[1:]), start=1):
        hot_duty = sum(interval_duty(stream, upper, lower) for stream in streams if stream.kind == "hot")
        cold_duty = sum(interval_duty(stream, upper, lower) for stream in streams if stream.kind == "cold")
        intervals.append(
            HeatCompositeInterval(
                interval_id=f"interval_{index:02d}",
                upper_temp_c=round(upper + hot_shift, 3),
                lower_temp_c=round(lower + hot_shift, 3),
                shifted_upper_temp_c=round(upper, 3),
                shifted_lower_temp_c=round(lower, 3),
                hot_duty_kw=round(hot_duty, 3),
                cold_duty_kw=round(cold_duty, 3),
                net_duty_kw=round(hot_duty - cold_duty, 3),
                notes="Screening composite interval derived from shifted hot/cold stream temperatures.",
                citations=sorted({citation for stream in streams for citation in stream.citations}),
                assumptions=sorted({assumption for stream in streams for assumption in stream.assumptions}),
            )
        )
    return intervals


def _service_cluster(unit_id: str) -> str:
    lowered = unit_id.lower()
    if any(token in lowered for token in ("reactor", "conv")):
        return "reaction"
    if any(token in lowered for token in ("absorp", "regen", "strip")):
        return "gas_treating"
    if any(token in lowered for token in ("purification", "concentration", "distill", "flash")):
        return "liquid_purification"
    if any(token in lowered for token in ("filtration", "drying", "crystal")):
        return "solids_finishing"
    return "balance_of_plant"


def _is_column_service_unit(unit_id: str) -> bool:
    lowered = unit_id.lower()
    return any(token in lowered for token in ("purification", "concentration", "regeneration", "distill", "strip", "drying"))


def _header_level_for_streams(
    hot_stream_ids: list[str],
    cold_stream_ids: list[str],
    heat_stream_lookup: dict[str, HeatStream],
) -> int:
    temperatures = [
        temperature
        for stream_id in hot_stream_ids + cold_stream_ids
        for temperature in (
            heat_stream_lookup[stream_id].supply_temp_c,
            heat_stream_lookup[stream_id].target_temp_c,
        )
        if stream_id in heat_stream_lookup
    ]
    if not temperatures:
        return 0
    characteristic_temp = max(temperatures)
    if characteristic_temp >= 165.0:
        return 1
    if characteristic_temp >= 115.0:
        return 2
    return 3


def _header_design_pressure_bar(header_level: int) -> float:
    return {
        1: 14.5,
        2: 11.0,
        3: 7.5,
    }.get(header_level, 6.0)


def _merge_island_envelopes(
    merged_id: str,
    topology: str,
    envelopes: list[_IslandEnvelope],
    *,
    architecture_role: str,
    header_level: int = 0,
    cluster_id: str | None = None,
) -> _IslandEnvelope:
    return _IslandEnvelope(
        island_id=merged_id,
        topology=topology,
        architecture_role=architecture_role,
        header_level=header_level,
        cluster_id=cluster_id,
        hot_stream_ids=sorted({stream_id for envelope in envelopes for stream_id in envelope.hot_stream_ids}),
        cold_stream_ids=sorted({stream_id for envelope in envelopes for stream_id in envelope.cold_stream_ids}),
        unit_ids=sorted({unit_id for envelope in envelopes for unit_id in envelope.unit_ids}),
        case_matches=[match for envelope in envelopes for match in envelope.case_matches],
        packet_candidates=[candidate for envelope in envelopes for candidate in envelope.packet_candidates],
        recoverable_potential_kw=round(sum(envelope.recoverable_potential_kw for envelope in envelopes), 3),
        selection_priority=round(sum(envelope.selection_priority for envelope in envelopes), 3),
        cross_service=any(envelope.cross_service for envelope in envelopes) or len({_service_cluster(unit_id) for envelope in envelopes for unit_id in envelope.unit_ids}) > 1,
    )


def _build_candidate_islands(
    case_id: str,
    topology: str,
    case_matches: list[HeatMatch],
    packet_candidates: list[HeatMatchCandidate],
    heat_stream_lookup: dict[str, HeatStream],
) -> list[_IslandEnvelope]:
    all_matches = list(case_matches) + [_as_heat_match(candidate) for candidate in packet_candidates]
    if not all_matches:
        return []
    adjacency: dict[str, set[str]] = {}
    for match in all_matches:
        adjacency.setdefault(match.hot_stream_id, set()).add(match.cold_stream_id)
        adjacency.setdefault(match.cold_stream_id, set()).add(match.hot_stream_id)

    envelopes: list[_IslandEnvelope] = []
    seen: set[str] = set()
    for seed_stream_id in adjacency:
        if seed_stream_id in seen:
            continue
        stack = [seed_stream_id]
        component_stream_ids: set[str] = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component_stream_ids.add(current)
            stack.extend(item for item in adjacency.get(current, set()) if item not in seen)
        hot_stream_ids = sorted(stream_id for stream_id in component_stream_ids if heat_stream_lookup.get(stream_id) and heat_stream_lookup[stream_id].kind == "hot")
        cold_stream_ids = sorted(stream_id for stream_id in component_stream_ids if heat_stream_lookup.get(stream_id) and heat_stream_lookup[stream_id].kind == "cold")
        island_case_matches = [
            match
            for match in case_matches
            if match.hot_stream_id in component_stream_ids and match.cold_stream_id in component_stream_ids
        ]
        island_packet_candidates = [
            candidate
            for candidate in packet_candidates
            if candidate.hot_stream_id in component_stream_ids and candidate.cold_stream_id in component_stream_ids
        ]
        unit_ids = sorted(
            {
                heat_stream_lookup[stream_id].source_unit_id
                for stream_id in component_stream_ids
                if stream_id in heat_stream_lookup
            }
        )
        hot_total = sum(heat_stream_lookup[stream_id].duty_kw for stream_id in hot_stream_ids if stream_id in heat_stream_lookup)
        cold_total = sum(heat_stream_lookup[stream_id].duty_kw for stream_id in cold_stream_ids if stream_id in heat_stream_lookup)
        candidate_total = sum(match.recovered_duty_kw for match in island_case_matches) + sum(candidate.recovered_duty_kw for candidate in island_packet_candidates)
        recoverable_potential_kw = round(min(hot_total, cold_total, candidate_total if candidate_total > 0.0 else min(hot_total, cold_total)), 3)
        service_clusters = {_service_cluster(unit_id) for unit_id in unit_ids}
        direct_match_count = sum(1 for match in island_case_matches if match.direct) + sum(
            1 for candidate in island_packet_candidates if "direct" in candidate.topology.lower()
        )
        cross_service = len(service_clusters) > 1
        selection_priority = round(
            recoverable_potential_kw
            * (
                1.0
                + (0.10 if cross_service else 0.0)
                + 0.03 * direct_match_count
                + 0.02 * len(unit_ids)
            ),
            3,
        )
        envelopes.append(
            _IslandEnvelope(
                island_id=f"{case_id}_island_{len(envelopes) + 1:02d}",
                topology=topology,
                hot_stream_ids=hot_stream_ids,
                cold_stream_ids=cold_stream_ids,
                unit_ids=unit_ids,
                case_matches=island_case_matches,
                packet_candidates=island_packet_candidates,
                recoverable_potential_kw=recoverable_potential_kw,
                selection_priority=selection_priority,
                cross_service=cross_service,
            )
        )
    return sorted(envelopes, key=lambda item: (item.selection_priority, item.recoverable_potential_kw), reverse=True)


def _build_variant_islands(
    case_id: str,
    topology: str,
    architecture_family: str,
    case_matches: list[HeatMatch],
    packet_candidates: list[HeatMatchCandidate],
    heat_stream_lookup: dict[str, HeatStream],
    composite_intervals: list[HeatCompositeInterval],
) -> list[_IslandEnvelope]:
    base_islands = _build_candidate_islands(
        case_id,
        topology,
        case_matches,
        packet_candidates,
        heat_stream_lookup,
    )
    if not base_islands:
        return []
    if architecture_family == "shared_htm":
        indirect_envelopes = [
            envelope
            for envelope in base_islands
            if envelope.packet_candidates
            or any(not match.direct for match in envelope.case_matches)
            or "htm" in topology.lower()
        ]
        if len(indirect_envelopes) >= 2:
            merged = _merge_island_envelopes(
                f"{case_id}_shared_htm_01",
                topology,
                indirect_envelopes,
                architecture_role="shared_htm",
                header_level=_header_level_for_streams(
                    [stream_id for envelope in indirect_envelopes for stream_id in envelope.hot_stream_ids],
                    [stream_id for envelope in indirect_envelopes for stream_id in envelope.cold_stream_ids],
                    heat_stream_lookup,
                ),
            )
            return [merged]
        return [
            _IslandEnvelope(
                island_id=envelope.island_id,
                topology=envelope.topology,
                hot_stream_ids=envelope.hot_stream_ids,
                cold_stream_ids=envelope.cold_stream_ids,
                unit_ids=envelope.unit_ids,
                architecture_role="shared_htm",
                header_level=_header_level_for_streams(envelope.hot_stream_ids, envelope.cold_stream_ids, heat_stream_lookup),
                cluster_id=None,
                case_matches=envelope.case_matches,
                packet_candidates=envelope.packet_candidates,
                recoverable_potential_kw=envelope.recoverable_potential_kw,
                selection_priority=envelope.selection_priority,
                cross_service=True,
            )
            for envelope in indirect_envelopes or base_islands[:1]
        ]
    if architecture_family == "condenser_reboiler_cluster":
        clustered = [
            envelope
            for envelope in base_islands
            if any(_is_column_service_unit(unit_id) for unit_id in envelope.unit_ids)
        ]
        if not clustered:
            return []
        merged = _merge_island_envelopes(
            f"{case_id}_cluster_01",
            topology,
            clustered,
            architecture_role="condenser_reboiler_cluster",
            header_level=_header_level_for_streams(
                [stream_id for envelope in clustered for stream_id in envelope.hot_stream_ids],
                [stream_id for envelope in clustered for stream_id in envelope.cold_stream_ids],
                heat_stream_lookup,
            ),
            cluster_id=f"{case_id}_cluster_01",
        )
        return [merged]
    if architecture_family == "staged_headers":
        staged: list[_IslandEnvelope] = []
        for envelope in base_islands:
            header_level = _header_level_for_streams(envelope.hot_stream_ids, envelope.cold_stream_ids, heat_stream_lookup)
            staged.append(
                _IslandEnvelope(
                    island_id=envelope.island_id,
                    topology=topology,
                    hot_stream_ids=envelope.hot_stream_ids,
                    cold_stream_ids=envelope.cold_stream_ids,
                    unit_ids=envelope.unit_ids,
                    architecture_role="staged_header",
                    header_level=header_level,
                    cluster_id=f"{case_id}_header_{header_level}",
                    case_matches=envelope.case_matches,
                    packet_candidates=envelope.packet_candidates,
                    recoverable_potential_kw=envelope.recoverable_potential_kw,
                    selection_priority=envelope.selection_priority + max(4 - header_level, 0) * 2.0,
                    cross_service=envelope.cross_service,
                )
            )
        if len({item.header_level for item in staged if item.header_level > 0}) < 2 and len(composite_intervals) >= 3:
            for index, envelope in enumerate(staged, start=1):
                envelope.header_level = 1 if index == 1 else 2
                envelope.cluster_id = f"{case_id}_header_{envelope.header_level}"
        return staged
    return base_islands


def _topology_variant_specs(
    case,
    base_topology: str,
    case_matches: list[HeatMatch],
    packet_candidates: list[HeatMatchCandidate],
    heat_stream_lookup: dict[str, HeatStream],
    composite_intervals: list[HeatCompositeInterval],
) -> list[tuple[str, str, str]]:
    specs: list[tuple[str, str, str]] = [(case.case_id, base_topology, "base")]
    hot_stream_ids = {match.hot_stream_id for match in case_matches} | {candidate.hot_stream_id for candidate in packet_candidates}
    cold_stream_ids = {match.cold_stream_id for match in case_matches} | {candidate.cold_stream_id for candidate in packet_candidates}
    if (
        case.recovered_duty_kw > 0.0
        and ("htm" in base_topology.lower() or any("htm" in candidate.topology.lower() for candidate in packet_candidates) or any(not match.direct for match in case_matches))
        and len(hot_stream_ids) >= 2
        and len(cold_stream_ids) >= 2
    ):
        specs.append((f"{case.case_id}__shared_htm", "shared HTM island network", "shared_htm"))
    if case.recovered_duty_kw > 0.0:
        hot_units = {
            heat_stream_lookup[stream_id].source_unit_id
            for stream_id in hot_stream_ids
            if stream_id in heat_stream_lookup
        }
        cold_units = {
            heat_stream_lookup[stream_id].source_unit_id
            for stream_id in cold_stream_ids
            if stream_id in heat_stream_lookup
        }
        if (
            ("htm" in base_topology.lower() or any(not match.direct for match in case_matches))
            and any(_is_column_service_unit(unit_id) for unit_id in hot_units)
            and any(_is_column_service_unit(unit_id) for unit_id in cold_units)
        ):
            specs.append((f"{case.case_id}__cond_reb_cluster", "condenser-reboiler cluster", "condenser_reboiler_cluster"))
    if case.recovered_duty_kw > 0.0 and (
        len(composite_intervals) >= 3
        or len(hot_stream_ids | cold_stream_ids) >= 4
    ):
        specs.append((f"{case.case_id}__staged_headers", "staged utility header network", "staged_headers"))
    return specs


def _allocate_island_targets(
    islands: list[_IslandEnvelope],
    total_target_recovered_duty_kw: float,
) -> list[_IslandEnvelope]:
    if not islands:
        return []
    target = max(total_target_recovered_duty_kw, 0.0)
    total_potential = sum(max(island.recoverable_potential_kw, 0.0) for island in islands)
    if target <= 0.0 or total_potential <= 0.0:
        return islands
    remaining_target = min(target, total_potential)
    for island in islands:
        proportional_share = (
            remaining_target * (island.recoverable_potential_kw / total_potential)
            if total_potential > 0.0
            else 0.0
        )
        island.target_recovered_duty_kw = round(min(island.recoverable_potential_kw, proportional_share), 3)
    assigned = sum(island.target_recovered_duty_kw for island in islands)
    remainder = max(remaining_target - assigned, 0.0)
    for island in islands:
        if remainder <= 0.5:
            break
        spare = max(island.recoverable_potential_kw - island.target_recovered_duty_kw, 0.0)
        if spare <= 0.0:
            continue
        increment = min(spare, remainder)
        island.target_recovered_duty_kw = round(island.target_recovered_duty_kw + increment, 3)
        remainder = max(remainder - increment, 0.0)
    return islands


def _materialize_selected_island(
    island: _IslandEnvelope,
    selected_matches: list[HeatMatch],
    train_steps: list[HeatExchangerTrainStep],
    heat_stream_lookup: dict[str, HeatStream],
) -> HeatUtilityIsland:
    component_stream_ids = set(island.hot_stream_ids) | set(island.cold_stream_ids)
    recovered_duty_kw = round(sum(step.recovered_duty_kw for step in train_steps), 3)
    hot_total = sum(heat_stream_lookup[stream_id].duty_kw for stream_id in island.hot_stream_ids if stream_id in heat_stream_lookup)
    cold_total = sum(heat_stream_lookup[stream_id].duty_kw for stream_id in island.cold_stream_ids if stream_id in heat_stream_lookup)
    service_clusters = {_service_cluster(unit_id) for unit_id in island.unit_ids}
    package_items = [package_item for step in train_steps for package_item in step.package_items]
    shared_htm_inventory_m3 = round(
        sum(
            package_item.volume_m3
            for package_item in package_items
            if package_item.package_role in {"circulation", "expansion", "header"}
        ),
        3,
    )
    header_design_pressure_bar = max(
        (
            package_item.design_pressure_bar
            for package_item in package_items
            if package_item.package_role == "header"
        ),
        default=_header_design_pressure_bar(island.header_level),
    )
    condenser_reboiler_pair_score = 0.0
    if island.architecture_role == "condenser_reboiler_cluster":
        hot_column_units = {
            heat_stream_lookup[stream_id].source_unit_id
            for stream_id in island.hot_stream_ids
            if stream_id in heat_stream_lookup and _is_column_service_unit(heat_stream_lookup[stream_id].source_unit_id)
        }
        cold_column_units = {
            heat_stream_lookup[stream_id].source_unit_id
            for stream_id in island.cold_stream_ids
            if stream_id in heat_stream_lookup and _is_column_service_unit(heat_stream_lookup[stream_id].source_unit_id)
        }
        condenser_reboiler_pair_score = round(
            min(len(hot_column_units), len(cold_column_units)) * 8.0
            + min(recovered_duty_kw / 20.0, 12.0)
            + (6.0 if island.cross_service else 0.0),
            3,
        )
    control_complexity_factor = round(
        len([package_item for package_item in package_items if package_item.package_role == "controls"]) * 0.9
        + len([package_item for package_item in package_items if package_item.package_role == "header"]) * 0.7
        + (1.2 if island.cross_service else 0.0)
        + max(island.header_level - 1, 0) * 0.5,
        3,
    )
    return HeatUtilityIsland(
        island_id=island.island_id,
        topology=island.topology,
        architecture_role=island.architecture_role,
        header_level=island.header_level,
        cluster_id=island.cluster_id,
        hot_stream_ids=island.hot_stream_ids,
        cold_stream_ids=island.cold_stream_ids,
        unit_ids=island.unit_ids,
        match_ids=[match.match_id for match in selected_matches],
        train_step_ids=[step.step_id for step in train_steps],
        candidate_match_count=len(island.case_matches) + len(island.packet_candidates),
        recoverable_potential_kw=round(island.recoverable_potential_kw, 3),
        target_recovered_duty_kw=round(island.target_recovered_duty_kw, 3),
        selection_priority=round(island.selection_priority, 3),
        shared_htm_inventory_m3=shared_htm_inventory_m3,
        header_design_pressure_bar=round(header_design_pressure_bar, 3),
        condenser_reboiler_pair_score=condenser_reboiler_pair_score,
        control_complexity_factor=control_complexity_factor,
        recovered_duty_kw=recovered_duty_kw,
        residual_hot_utility_kw=round(max(hot_total - recovered_duty_kw, 0.0), 3),
        residual_cold_utility_kw=round(max(cold_total - recovered_duty_kw, 0.0), 3),
        direct_match_count=sum(1 for match in selected_matches if match.direct),
        indirect_match_count=sum(1 for match in selected_matches if not match.direct),
        cross_service=len(service_clusters) > 1,
        notes=(
            f"Island-aware selection balanced {len(component_stream_ids)} thermal streams across service clusters: {', '.join(sorted(service_clusters))}. "
            f"Architecture role={island.architecture_role}; header level={island.header_level or 'n/a'}; "
            f"header pressure={header_design_pressure_bar:.1f} bar."
        ),
        citations=sorted({citation for step in train_steps for citation in step.citations}),
        assumptions=sorted({assumption for step in train_steps for assumption in step.assumptions}),
    )


def _compatible_packet_candidates(topology: str, candidates: list[HeatMatchCandidate]) -> list[HeatMatchCandidate]:
    lowered = topology.lower()
    if "shared htm" in lowered or "htm" in lowered:
        return [candidate for candidate in candidates if "htm" in candidate.topology.lower()]
    if "condenser-reboiler" in lowered:
        return [candidate for candidate in candidates if any(token in candidate.cold_stream_id.lower() or token in candidate.hot_stream_id.lower() for token in ("purification", "concentration", "regeneration", "drying"))]
    if "header" in lowered:
        return candidates
    if "direct" in lowered or "multi" in lowered:
        return [candidate for candidate in candidates if "direct" in candidate.topology.lower()]
    return candidates


def _as_heat_match(candidate: HeatMatchCandidate) -> HeatMatch:
    return HeatMatch(
        match_id=candidate.candidate_id,
        hot_stream_id=candidate.hot_stream_id,
        cold_stream_id=candidate.cold_stream_id,
        recovered_duty_kw=candidate.recovered_duty_kw,
        direct="direct" in candidate.topology.lower(),
        medium="direct" if "direct" in candidate.topology.lower() else "Dowtherm A",
        min_approach_temp_c=20.0,
        notes=candidate.notes,
        citations=candidate.citations,
        assumptions=candidate.assumptions,
    )


def _step_lmtd_k(hot_stream: HeatStream | None, cold_stream: HeatStream | None) -> float:
    if hot_stream is None or cold_stream is None:
        return 18.0
    dt1 = max(hot_stream.supply_temp_c - cold_stream.target_temp_c, 8.0)
    dt2 = max(hot_stream.target_temp_c - cold_stream.supply_temp_c, 8.0)
    if abs(dt1 - dt2) <= 1e-6:
        return dt1
    ratio = max(dt1 / max(dt2, 1e-6), 1.0001)
    return max((dt1 - dt2) / math.log(ratio), 8.0)


def _package_family(step: HeatExchangerTrainStep) -> str:
    service = step.service.lower()
    if "reboiler" in service or any(token in step.sink_unit_id.lower() for token in ("purification", "concentration", "regeneration", "drying")):
        return "reboiler"
    if "condenser" in service or any(token in step.source_unit_id.lower() for token in ("purification", "concentration", "regeneration", "drying")):
        return "condenser"
    if any(token in step.source_unit_id.lower() for token in ("r-101", "conv-101", "reactor")):
        return "reactor_coupling"
    return "process_exchange"


def _train_step(
    case_id: str,
    index: int,
    topology: str,
    match: HeatMatch,
    heat_stream_lookup: dict[str, HeatStream],
    *,
    header_level: int = 0,
    cluster_id: str | None = None,
) -> HeatExchangerTrainStep:
    hot_stream = heat_stream_lookup.get(match.hot_stream_id)
    cold_stream = heat_stream_lookup.get(match.cold_stream_id)
    source_unit = hot_stream.source_unit_id if hot_stream is not None else "unknown_hot_source"
    sink_unit = cold_stream.source_unit_id if cold_stream is not None else "unknown_cold_sink"
    return HeatExchangerTrainStep(
        step_id=f"{case_id}_step_{index:02d}",
        exchanger_id=f"HX-{index:02d}",
        cluster_id=cluster_id,
        header_level=header_level,
        topology=topology,
        service=f"{source_unit} to {sink_unit} heat recovery",
        hot_stream_id=match.hot_stream_id,
        cold_stream_id=match.cold_stream_id,
        source_unit_id=source_unit,
        sink_unit_id=sink_unit,
        recovered_duty_kw=match.recovered_duty_kw,
        medium=match.medium,
        notes=match.notes,
        citations=sorted(set(match.citations + (hot_stream.citations if hot_stream else []) + (cold_stream.citations if cold_stream else []))),
        assumptions=sorted(set(match.assumptions + (hot_stream.assumptions if hot_stream else []) + (cold_stream.assumptions if cold_stream else []))),
    )


def _package_items_for_step(
    step: HeatExchangerTrainStep,
    heat_stream_lookup: dict[str, HeatStream],
    *,
    include_network_package: bool = False,
) -> list[UtilityTrainPackageItem]:
    hot_stream = heat_stream_lookup.get(step.hot_stream_id)
    cold_stream = heat_stream_lookup.get(step.cold_stream_id)
    family = _package_family(step)
    max_temp = max(
        hot_stream.supply_temp_c if hot_stream else 120.0,
        cold_stream.target_temp_c if cold_stream else 90.0,
    )
    direct = step.medium.lower() == "direct"
    lmtd_k = _step_lmtd_k(hot_stream, cold_stream)
    header_pressure_bar = _header_design_pressure_bar(step.header_level)
    if family == "reboiler":
        u_value = 700.0 if direct else 600.0
        latent_kj_kg = 1850.0
        phase_change_load = step.recovered_duty_kw * 3600.0 / latent_kj_kg
        circulation_ratio = 3.2 if direct else 4.8 if "shared htm" in step.topology.lower() else 4.5
        circulation_flow = max((phase_change_load * circulation_ratio) / 880.0, 1.5)
    elif family == "condenser":
        u_value = 820.0 if direct else 660.0
        latent_kj_kg = 2100.0
        phase_change_load = step.recovered_duty_kw * 3600.0 / latent_kj_kg
        circulation_ratio = 1.0
        circulation_flow = max(phase_change_load / 940.0, 1.0)
    else:
        u_value = 560.0 if direct else 470.0
        cp_kj_kg_k = 2.6 if not direct else 3.2
        delta_t = max((hot_stream.supply_temp_c - hot_stream.target_temp_c) if hot_stream else 18.0, 12.0)
        phase_change_load = 0.0
        circulation_ratio = 1.0 if direct else 2.2
        circulation_flow = max((step.recovered_duty_kw * 3600.0 / max(cp_kj_kg_k * delta_t, 1.0)) / 950.0 * circulation_ratio, 0.8)
    exchanger_area = max((step.recovered_duty_kw * 1000.0) / max(u_value * lmtd_k, 1.0), 1.0)
    exchanger_volume = max(exchanger_area * (0.085 if family == "reboiler" else 0.070 if family == "condenser" else 0.060), 0.6)
    exchanger = UtilityTrainPackageItem(
        package_item_id=f"{step.step_id}_exchanger",
        parent_step_id=step.step_id,
        cluster_id=step.cluster_id,
        header_level=step.header_level,
        package_role="exchanger",
        equipment_id=step.exchanger_id,
        equipment_type=(
            "Kettle reboiler package"
            if family == "reboiler" and direct
            else "HTM reboiler package"
            if family == "reboiler"
            else "Surface condenser package"
            if family == "condenser" and direct
            else "HTM condenser package"
            if family == "condenser"
            else "Heat integration exchanger"
            if direct
            else "HTM loop exchanger"
        ),
        service=step.service,
        package_family=family,
        design_temperature_c=round(max_temp + (12.0 if direct else 18.0), 2),
        design_pressure_bar=round(6.5 if direct else 11.0, 2),
        volume_m3=round(exchanger_volume, 3),
        duty_kw=round(step.recovered_duty_kw, 3),
        flow_m3_hr=round(circulation_flow, 3),
        lmtd_k=round(lmtd_k, 3),
        heat_transfer_area_m2=round(exchanger_area, 3),
        phase_change_load_kg_hr=round(phase_change_load, 3),
        circulation_ratio=round(circulation_ratio, 3),
        material_of_construction="SS316" if direct else "Carbon steel",
        notes="Primary exchanger item derived from selected utility-train step.",
        citations=step.citations,
        assumptions=step.assumptions,
    )
    controls = UtilityTrainPackageItem(
        package_item_id=f"{step.step_id}_controls",
        parent_step_id=step.step_id,
        cluster_id=step.cluster_id,
        header_level=step.header_level,
        package_role="controls",
        equipment_id=f"{step.exchanger_id}-CTRL",
        equipment_type="Utility control package",
        service=f"{step.service} control valves, instrumentation, and bypass station",
        package_family=family,
        design_temperature_c=round(max_temp + 8.0, 2),
        design_pressure_bar=round(5.0 if direct else 9.0, 2),
        volume_m3=0.15,
        flow_m3_hr=round(circulation_flow, 3),
        material_of_construction="Carbon steel",
        notes="Includes control valve station, bypass, and instrumentation package for the selected train step.",
        citations=step.citations,
        assumptions=step.assumptions,
    )
    items = [exchanger, controls]
    if include_network_package and ("header" in step.topology.lower() or "shared htm" in step.topology.lower() or "cluster" in step.topology.lower()):
        items.append(
            UtilityTrainPackageItem(
                package_item_id=f"{step.step_id}_header",
                parent_step_id=step.step_id,
                cluster_id=step.cluster_id,
                header_level=step.header_level,
        package_role="header",
        equipment_id=f"{step.exchanger_id}-HDR",
        equipment_type=(
            "Shared HTM header manifold"
            if "shared htm" in step.topology.lower()
                    else "Condenser-reboiler header station"
                    if "cluster" in step.topology.lower()
                    else "Staged utility header station"
                ),
                service=f"{step.service} network header and isolation package",
        package_family=family,
        design_temperature_c=round(max_temp + 10.0, 2),
        design_pressure_bar=round(max(header_pressure_bar, 8.0 if direct else 11.5), 2),
        volume_m3=round(max(step.recovered_duty_kw / 40000.0, 0.20), 3),
        duty_kw=round(step.recovered_duty_kw, 3),
        flow_m3_hr=round(circulation_flow, 3),
        material_of_construction="Carbon steel",
        notes="Network-level header/manifold package added for richer heat-network architecture.",
                citations=step.citations,
                assumptions=step.assumptions,
            )
        )
    if not direct:
        circulation_power_kw = max(step.recovered_duty_kw / 2200.0, 2.5)
        items.extend(
            [
                UtilityTrainPackageItem(
                    package_item_id=f"{step.step_id}_circulation",
                    parent_step_id=step.step_id,
                    cluster_id=step.cluster_id,
                    header_level=step.header_level,
                    package_role="circulation",
                    equipment_id=f"{step.exchanger_id}-PMP",
                    equipment_type="HTM circulation skid",
                    service=f"{step.service} circulation loop",
                    package_family=family,
                    design_temperature_c=round(max_temp + 10.0, 2),
                    design_pressure_bar=round(max(header_pressure_bar, 12.0), 2),
                    volume_m3=0.25,
                    power_kw=round(circulation_power_kw, 3),
                    flow_m3_hr=round(circulation_flow, 3),
                    circulation_ratio=round(circulation_ratio, 3),
                    material_of_construction="Carbon steel",
                    notes="HTM circulation skid sized from recovered duty and selected train topology.",
                    citations=step.citations,
                    assumptions=step.assumptions,
                ),
                UtilityTrainPackageItem(
                    package_item_id=f"{step.step_id}_expansion",
                    parent_step_id=step.step_id,
                    cluster_id=step.cluster_id,
                    header_level=step.header_level,
                    package_role="expansion",
                    equipment_id=f"{step.exchanger_id}-EXP",
                    equipment_type="HTM expansion tank",
                    service=f"{step.service} HTM expansion and inventory hold-up",
                    package_family=family,
                    design_temperature_c=round(max_temp + 15.0, 2),
                    design_pressure_bar=6.0,
                    volume_m3=round(max(step.recovered_duty_kw / (12000.0 if "shared htm" in step.topology.lower() else 14000.0), 1.0), 3),
                    flow_m3_hr=round(circulation_flow, 3),
                    material_of_construction="Carbon steel",
                    notes="Expansion volume estimated from recovered duty and HTM loop inventory basis.",
                    citations=step.citations,
                    assumptions=step.assumptions,
                ),
                UtilityTrainPackageItem(
                    package_item_id=f"{step.step_id}_relief",
                    parent_step_id=step.step_id,
                    cluster_id=step.cluster_id,
                    header_level=step.header_level,
                    package_role="relief",
                    equipment_id=f"{step.exchanger_id}-RV",
                    equipment_type="HTM relief package",
                    service=f"{step.service} thermal relief and collection package",
                    package_family=family,
                    design_temperature_c=round(max_temp + 18.0, 2),
                    design_pressure_bar=13.5,
                    volume_m3=round(max(step.recovered_duty_kw / 26000.0, 0.35), 3),
                    flow_m3_hr=round(circulation_flow, 3),
                    material_of_construction="Carbon steel",
                    notes="Relief package includes relief device and small knock-out volume for HTM overpressure screening.",
                    citations=step.citations,
                    assumptions=step.assumptions,
                ),
            ]
        )
    return items


def _synthesize_selected_train(
    case_id: str,
    topology: str,
    case_matches: list[HeatMatch],
    packet_candidates: list[HeatMatchCandidate],
    heat_stream_lookup: dict[str, HeatStream],
    target_recovered_duty_kw: float,
    *,
    island_id: str | None = None,
    header_level: int = 0,
    cluster_id: str | None = None,
    start_index: int = 1,
) -> tuple[list[HeatMatch], list[HeatExchangerTrainStep]]:
    selected_matches: list[HeatMatch] = []
    selected_pairs: set[tuple[str, str]] = set()
    local_stream_ids = {
        match.hot_stream_id
        for match in case_matches
    } | {
        match.cold_stream_id
        for match in case_matches
    } | {
        candidate.hot_stream_id
        for candidate in packet_candidates
    } | {
        candidate.cold_stream_id
        for candidate in packet_candidates
    }
    remaining_hot = {
        stream_id: stream.duty_kw
        for stream_id, stream in heat_stream_lookup.items()
        if stream.kind == "hot" and (not local_stream_ids or stream_id in local_stream_ids)
    }
    remaining_cold = {
        stream_id: stream.duty_kw
        for stream_id, stream in heat_stream_lookup.items()
        if stream.kind == "cold" and (not local_stream_ids or stream_id in local_stream_ids)
    }
    remaining_target = max(target_recovered_duty_kw, 0.0)

    def allocate(match: HeatMatch) -> HeatMatch | None:
        nonlocal remaining_target
        pair = (match.hot_stream_id, match.cold_stream_id)
        if pair in selected_pairs:
            return None
        hot_capacity = remaining_hot.get(match.hot_stream_id, match.recovered_duty_kw)
        cold_capacity = remaining_cold.get(match.cold_stream_id, match.recovered_duty_kw)
        allocation = min(
            match.recovered_duty_kw,
            hot_capacity,
            cold_capacity,
            remaining_target if remaining_target > 0.0 else match.recovered_duty_kw,
        )
        if allocation <= 1.0:
            return None
        remaining_hot[match.hot_stream_id] = max(hot_capacity - allocation, 0.0)
        remaining_cold[match.cold_stream_id] = max(cold_capacity - allocation, 0.0)
        remaining_target = max(remaining_target - allocation, 0.0)
        selected_pairs.add(pair)
        return HeatMatch(
            match_id=match.match_id,
            hot_stream_id=match.hot_stream_id,
            cold_stream_id=match.cold_stream_id,
            recovered_duty_kw=round(allocation, 3),
            direct=match.direct,
            medium=match.medium,
            min_approach_temp_c=match.min_approach_temp_c,
            notes=match.notes,
            citations=match.citations,
            assumptions=match.assumptions,
        )

    for match in case_matches:
        allocated = allocate(match)
        if allocated is not None:
            selected_matches.append(allocated)

    for candidate in sorted(packet_candidates, key=lambda item: item.recovered_duty_kw, reverse=True):
        if remaining_target <= 1.0:
            break
        allocated = allocate(_as_heat_match(candidate))
        if allocated is not None:
            selected_matches.append(allocated)

    train_steps = []
    for offset, match in enumerate(selected_matches):
        step = _train_step(
            case_id,
            start_index + offset,
            topology,
            match,
            heat_stream_lookup,
            header_level=header_level,
            cluster_id=cluster_id,
        )
        step.island_id = island_id
        step.package_items = _package_items_for_step(
            step,
            heat_stream_lookup,
            include_network_package=offset == 0,
        )
        for package_item in step.package_items:
            package_item.island_id = island_id
        train_steps.append(step)
    return selected_matches, train_steps


def _network_case_selection_score(case: HeatNetworkCase) -> float:
    family_bonus = {
        "shared_htm": 12.0,
        "condenser_reboiler_cluster": 10.0,
        "staged_headers": 8.0,
        "base": 0.0,
    }.get(case.architecture_family, 0.0)
    return round(
        case.recovered_duty_kw
        + family_bonus
        + case.shared_htm_island_count * 2.0
        + case.condenser_reboiler_cluster_count * 2.5
        + case.header_count * 1.5
        - case.exchanger_count * 0.35
        - case.residual_hot_utility_kw * 0.01
        - case.residual_cold_utility_kw * 0.005,
        3,
    )


def build_utility_architecture_decision(
    utility_network_decision: UtilityNetworkDecision,
    energy_balance: EnergyBalance | None = None,
) -> UtilityArchitectureDecision:
    min_approach_temp_c = min(
        [
            match.min_approach_temp_c
            for case in utility_network_decision.cases
            for match in case.heat_matches
            if match.min_approach_temp_c > 0.0
        ]
        or [20.0]
    )
    packet_heat_streams = _packet_heat_streams(energy_balance)
    heat_stream_map = {stream.stream_id: stream for stream in utility_network_decision.heat_streams}
    for stream in packet_heat_streams:
        heat_stream_map.setdefault(stream.stream_id, stream)
    all_heat_streams = list(heat_stream_map.values())
    heat_stream_lookup = {stream.stream_id: stream for stream in all_heat_streams}
    hot_streams = [stream for stream in all_heat_streams if stream.kind == "hot"]
    cold_streams = [stream for stream in all_heat_streams if stream.kind == "cold"]
    composite_intervals = _build_composite_intervals(
        all_heat_streams,
        min_approach_temp_c,
    )
    heat_stream_set = HeatStreamSet(
        route_id=utility_network_decision.route_id,
        hot_streams=hot_streams,
        cold_streams=cold_streams,
        composite_intervals=composite_intervals,
        pinch_temp_c=utility_network_decision.utility_target.pinch_temp_c,
        markdown="\n".join(
            [
                "| Stream | Kind | Source Unit | Supply (C) | Target (C) | Duty (kW) |",
                "| --- | --- | --- | --- | --- | --- |",
                *[
                    f"| {stream.stream_id} | {stream.kind} | {stream.source_unit_id} | {stream.supply_temp_c:.1f} | {stream.target_temp_c:.1f} | {stream.duty_kw:.3f} |"
                    for stream in all_heat_streams
                ],
                "",
                "| Interval | Shifted Upper (C) | Shifted Lower (C) | Hot Duty (kW) | Cold Duty (kW) | Net Duty (kW) |",
                "| --- | --- | --- | --- | --- | --- |",
                *[
                    f"| {interval.interval_id} | {interval.shifted_upper_temp_c:.1f} | {interval.shifted_lower_temp_c:.1f} | {interval.hot_duty_kw:.3f} | {interval.cold_duty_kw:.3f} | {interval.net_duty_kw:.3f} |"
                    for interval in composite_intervals
                ],
            ]
        ),
        citations=utility_network_decision.citations,
        assumptions=utility_network_decision.assumptions + (
            ["Utility architecture augmented with solved unit thermal packets."] if packet_heat_streams else []
        ),
    )
    packet_candidates = _packet_match_candidates(energy_balance)
    network_cases: list[HeatNetworkCase] = []
    for case in utility_network_decision.cases:
        topology = _topology_label(case.case_id, case.title)
        for variant_case_id, variant_topology, architecture_family in _topology_variant_specs(
            case,
            topology,
            case.heat_matches,
            _compatible_packet_candidates(topology, packet_candidates),
            heat_stream_lookup,
            composite_intervals,
        ):
            compatible_packet_candidates = _compatible_packet_candidates(variant_topology, packet_candidates)
            candidates = [
                HeatMatchCandidate(
                    candidate_id=f"{variant_case_id}_{match.match_id}",
                    hot_stream_id=match.hot_stream_id,
                    cold_stream_id=match.cold_stream_id,
                    topology=variant_topology,
                    recovered_duty_kw=match.recovered_duty_kw,
                    feasible=case.feasible,
                    notes=match.notes,
                    citations=match.citations,
                    assumptions=match.assumptions,
                )
                for match in case.heat_matches
            ]
            candidates.extend(
                candidate
                for candidate in compatible_packet_candidates
                if candidate.candidate_id not in {existing.candidate_id for existing in candidates}
            )
            candidate_islands = _allocate_island_targets(
                _build_variant_islands(
                    variant_case_id,
                    variant_topology,
                    architecture_family,
                    case.heat_matches,
                    compatible_packet_candidates,
                    heat_stream_lookup,
                    composite_intervals,
                ),
                case.recovered_duty_kw,
            )
            selected_matches: list[HeatMatch] = []
            selected_train_steps: list[HeatExchangerTrainStep] = []
            utility_islands: list[HeatUtilityIsland] = []
            next_step_index = 1
            for island in candidate_islands:
                if island.target_recovered_duty_kw <= 1.0:
                    continue
                island_matches, island_steps = _synthesize_selected_train(
                    variant_case_id,
                    variant_topology,
                    island.case_matches,
                    island.packet_candidates,
                    heat_stream_lookup,
                    island.target_recovered_duty_kw,
                    island_id=island.island_id,
                    header_level=island.header_level,
                    cluster_id=island.cluster_id,
                    start_index=next_step_index,
                )
                next_step_index += len(island_steps)
                if not island_matches:
                    continue
                selected_matches.extend(island_matches)
                selected_train_steps.extend(island_steps)
                utility_islands.append(
                    _materialize_selected_island(
                        island,
                        island_matches,
                        island_steps,
                        heat_stream_lookup,
                    )
                )
            if not utility_islands and case.recovered_duty_kw > 0.0:
                fallback_header_level = _header_level_for_streams(
                    sorted({match.hot_stream_id for match in case.heat_matches}),
                    sorted({match.cold_stream_id for match in case.heat_matches}),
                    heat_stream_lookup,
                )
                fallback_cluster_id = f"{variant_case_id}_cluster_01" if architecture_family == "condenser_reboiler_cluster" else (
                    f"{variant_case_id}_header_{fallback_header_level}" if architecture_family == "staged_headers" else None
                )
                fallback_matches, fallback_steps = _synthesize_selected_train(
                    variant_case_id,
                    variant_topology,
                    case.heat_matches,
                    compatible_packet_candidates,
                    heat_stream_lookup,
                    case.recovered_duty_kw,
                    island_id=f"{variant_case_id}_island_01",
                    header_level=fallback_header_level if architecture_family != "base" else 0,
                    cluster_id=fallback_cluster_id,
                    start_index=1,
                )
                selected_matches = fallback_matches
                selected_train_steps = fallback_steps
                if fallback_matches:
                    utility_islands = [
                        _materialize_selected_island(
                            _IslandEnvelope(
                                island_id=f"{variant_case_id}_island_01",
                                topology=variant_topology,
                                hot_stream_ids=sorted({match.hot_stream_id for match in fallback_matches}),
                                cold_stream_ids=sorted({match.cold_stream_id for match in fallback_matches}),
                                unit_ids=sorted(
                                    {
                                        heat_stream_lookup[stream_id].source_unit_id
                                        for stream_id in {match.hot_stream_id for match in fallback_matches} | {match.cold_stream_id for match in fallback_matches}
                                        if stream_id in heat_stream_lookup
                                    }
                                ),
                                architecture_role=(
                                    "shared_htm"
                                    if architecture_family == "shared_htm"
                                    else "condenser_reboiler_cluster"
                                    if architecture_family == "condenser_reboiler_cluster"
                                    else "staged_header"
                                    if architecture_family == "staged_headers"
                                    else "generic"
                                ),
                                header_level=fallback_header_level if architecture_family != "base" else 0,
                                cluster_id=fallback_cluster_id,
                                case_matches=case.heat_matches,
                                packet_candidates=compatible_packet_candidates,
                                recoverable_potential_kw=case.recovered_duty_kw,
                                target_recovered_duty_kw=case.recovered_duty_kw,
                                selection_priority=case.recovered_duty_kw,
                                cross_service=architecture_family in {"shared_htm", "condenser_reboiler_cluster"},
                            ),
                            fallback_matches,
                            fallback_steps,
                            heat_stream_lookup,
                        )
                    ]
            header_count = len({island.header_level for island in utility_islands if island.header_level > 0})
            shared_htm_count = sum(1 for island in utility_islands if island.architecture_role == "shared_htm")
            cond_reb_cluster_count = len({island.cluster_id for island in utility_islands if island.cluster_id and island.architecture_role == "condenser_reboiler_cluster"})
            network_case = HeatNetworkCase(
                case_id=variant_case_id,
                base_case_id=case.case_id,
                topology=variant_topology,
                architecture_family=architecture_family,
                recovered_duty_kw=case.recovered_duty_kw,
                residual_hot_utility_kw=case.residual_hot_utility_kw,
                residual_cold_utility_kw=case.residual_cold_utility_kw,
                exchanger_count=len(selected_train_steps),
                header_count=header_count,
                shared_htm_island_count=shared_htm_count,
                condenser_reboiler_cluster_count=cond_reb_cluster_count,
                match_candidates=candidates,
                selected_matches=selected_matches,
                utility_islands=utility_islands,
                selected_train_steps=selected_train_steps,
                markdown=(case.summary or case.title)
                + (
                    "\n\n"
                    + "\n".join(
                        f"- {step.exchanger_id}: {step.service} via {step.medium}, {step.recovered_duty_kw:.3f} kW"
                        for step in selected_train_steps
                    )
                    if selected_train_steps
                    else "\n\n- No exchanger train selected; case relies on purchased utilities."
                )
                + (
                    "\n\n"
                    + "\n".join(
                        f"- {island.island_id}: role={island.architecture_role}; header={island.header_level or 'n/a'}; cluster={island.cluster_id or '-'}; "
                        f"target {island.target_recovered_duty_kw:.3f} kW / recovered {island.recovered_duty_kw:.3f} kW / potential {island.recoverable_potential_kw:.3f} kW"
                        for island in utility_islands
                    )
                    if utility_islands
                    else ""
                ),
                citations=case.citations,
                assumptions=case.assumptions,
            )
            network_case.selection_score = _network_case_selection_score(network_case)
            network_cases.append(network_case)
    selected_base_case_id = utility_network_decision.selected_case_id
    selected_family_cases = [case for case in network_cases if case.base_case_id == selected_base_case_id]
    selected_case = (
        max(selected_family_cases, key=lambda item: item.selection_score)
        if selected_family_cases
        else next(
            (case for case in network_cases if case.case_id == utility_network_decision.selected_case_id),
            network_cases[0] if network_cases else None,
        )
    )
    architecture = HeatNetworkArchitecture(
        route_id=utility_network_decision.route_id,
        selected_case_id=selected_case.case_id if selected_case else utility_network_decision.selected_case_id,
        heat_stream_set=heat_stream_set,
        cases=network_cases,
        selected_island_ids=[island.island_id for island in (selected_case.utility_islands if selected_case else [])],
        selected_train_steps=selected_case.selected_train_steps if selected_case else [],
        selected_package_items=[item for step in (selected_case.selected_train_steps if selected_case else []) for item in step.package_items],
        topology_summary=(
            f"{selected_case.topology} ({selected_case.architecture_family}) with {len(selected_case.utility_islands)} utility islands"
            if selected_case
            else "no architecture selected"
        ),
        markdown="\n".join(
            [
                f"Selected topology: {selected_case.topology if selected_case else 'n/a'}",
                f"Selected architecture family: {selected_case.architecture_family if selected_case else 'n/a'}",
                "",
                f"Recovered duty: {selected_case.recovered_duty_kw:.3f} kW" if selected_case else "Recovered duty: n/a",
                f"Residual hot utility: {selected_case.residual_hot_utility_kw:.3f} kW" if selected_case else "Residual hot utility: n/a",
                f"Packet-level thermal candidates: {len(packet_candidates)}" if energy_balance is not None else "",
                f"Composite intervals: {len(composite_intervals)}",
                f"Utility islands: {len(selected_case.utility_islands)}" if selected_case else "Utility islands: 0",
                f"Header levels: {selected_case.header_count}" if selected_case else "Header levels: 0",
                f"Shared HTM islands: {selected_case.shared_htm_island_count}" if selected_case else "Shared HTM islands: 0",
                f"Condenser-reboiler clusters: {selected_case.condenser_reboiler_cluster_count}" if selected_case else "Condenser-reboiler clusters: 0",
                f"Selected exchanger train steps: {len(selected_case.selected_train_steps)}" if selected_case else "Selected exchanger train steps: 0",
                f"Selected package items: {sum(len(step.package_items) for step in (selected_case.selected_train_steps if selected_case else []))}",
                *[
                    f"- {step.exchanger_id}: {step.service} via {step.medium}, {step.recovered_duty_kw:.3f} kW; header={step.header_level or 'n/a'}; cluster={step.cluster_id or '-'}"
                    for step in (selected_case.selected_train_steps if selected_case else [])
                ],
            ]
        ),
        citations=utility_network_decision.citations,
        assumptions=utility_network_decision.assumptions,
    )
    markdown = "\n".join(
        [
            f"Selected utility architecture: {architecture.topology_summary}.",
            "",
            f"Selected case id: {architecture.selected_case_id or 'n/a'}",
            f"Selected base case id: {selected_case.base_case_id if selected_case else 'n/a'}",
            f"Recoverable duty target: {utility_network_decision.utility_target.recoverable_duty_kw:.3f} kW",
            f"Selected annual utility cost: INR {utility_network_decision.selected_annual_utility_cost_inr:,.2f}/y",
            f"Thermal packet count: {len(energy_balance.unit_thermal_packets)}" if energy_balance is not None else "",
            f"Packet-derived exchanger candidates: {len(packet_candidates)}" if packet_candidates else "",
            f"Composite intervals: {len(composite_intervals)}",
            f"Selected utility islands: {len(architecture.selected_island_ids)}",
            f"Selected train steps: {len(architecture.selected_train_steps)}",
        ]
    )
    return UtilityArchitectureDecision(
        route_id=utility_network_decision.route_id,
        architecture=architecture,
        decision=utility_network_decision.decision,
        markdown=markdown,
        citations=utility_network_decision.citations,
        assumptions=utility_network_decision.assumptions,
    )
