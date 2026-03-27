from __future__ import annotations

import math

from aoc.models import (
    EnergyBalance,
    HeatExchangerTrainStep,
    HeatMatch,
    HeatMatchCandidate,
    HeatNetworkArchitecture,
    HeatNetworkCase,
    HeatStream,
    HeatStreamSet,
    UtilityTrainPackageItem,
    UtilityArchitectureDecision,
    UtilityNetworkDecision,
)


def _topology_label(case_id: str, title: str) -> str:
    lowered = f"{case_id} {title}".lower()
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


def _compatible_packet_candidates(topology: str, candidates: list[HeatMatchCandidate]) -> list[HeatMatchCandidate]:
    lowered = topology.lower()
    if "htm" in lowered:
        return [candidate for candidate in candidates if "htm" in candidate.topology.lower()]
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
) -> HeatExchangerTrainStep:
    hot_stream = heat_stream_lookup.get(match.hot_stream_id)
    cold_stream = heat_stream_lookup.get(match.cold_stream_id)
    source_unit = hot_stream.source_unit_id if hot_stream is not None else "unknown_hot_source"
    sink_unit = cold_stream.source_unit_id if cold_stream is not None else "unknown_cold_sink"
    return HeatExchangerTrainStep(
        step_id=f"{case_id}_step_{index:02d}",
        exchanger_id=f"HX-{index:02d}",
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
    if family == "reboiler":
        u_value = 700.0 if direct else 600.0
        latent_kj_kg = 1850.0
        phase_change_load = step.recovered_duty_kw * 3600.0 / latent_kj_kg
        circulation_ratio = 3.2 if direct else 4.5
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
    if not direct:
        circulation_power_kw = max(step.recovered_duty_kw / 2200.0, 2.5)
        items.extend(
            [
                UtilityTrainPackageItem(
                    package_item_id=f"{step.step_id}_circulation",
                    parent_step_id=step.step_id,
                    package_role="circulation",
                    equipment_id=f"{step.exchanger_id}-PMP",
                    equipment_type="HTM circulation skid",
                    service=f"{step.service} circulation loop",
                    package_family=family,
                    design_temperature_c=round(max_temp + 10.0, 2),
                    design_pressure_bar=12.0,
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
                    package_role="expansion",
                    equipment_id=f"{step.exchanger_id}-EXP",
                    equipment_type="HTM expansion tank",
                    service=f"{step.service} HTM expansion and inventory hold-up",
                    package_family=family,
                    design_temperature_c=round(max_temp + 15.0, 2),
                    design_pressure_bar=6.0,
                    volume_m3=round(max(step.recovered_duty_kw / 14000.0, 1.0), 3),
                    flow_m3_hr=round(circulation_flow, 3),
                    material_of_construction="Carbon steel",
                    notes="Expansion volume estimated from recovered duty and HTM loop inventory basis.",
                    citations=step.citations,
                    assumptions=step.assumptions,
                ),
                UtilityTrainPackageItem(
                    package_item_id=f"{step.step_id}_relief",
                    parent_step_id=step.step_id,
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
) -> tuple[list[HeatMatch], list[HeatExchangerTrainStep]]:
    selected_matches: list[HeatMatch] = []
    selected_pairs: set[tuple[str, str]] = set()
    remaining_hot = {stream_id: stream.duty_kw for stream_id, stream in heat_stream_lookup.items() if stream.kind == "hot"}
    remaining_cold = {stream_id: stream.duty_kw for stream_id, stream in heat_stream_lookup.items() if stream.kind == "cold"}
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
    for index, match in enumerate(selected_matches, start=1):
        step = _train_step(case_id, index, topology, match, heat_stream_lookup)
        step.package_items = _package_items_for_step(step, heat_stream_lookup)
        train_steps.append(step)
    return selected_matches, train_steps


def build_utility_architecture_decision(
    utility_network_decision: UtilityNetworkDecision,
    energy_balance: EnergyBalance | None = None,
) -> UtilityArchitectureDecision:
    packet_heat_streams = _packet_heat_streams(energy_balance)
    heat_stream_map = {stream.stream_id: stream for stream in utility_network_decision.heat_streams}
    for stream in packet_heat_streams:
        heat_stream_map.setdefault(stream.stream_id, stream)
    all_heat_streams = list(heat_stream_map.values())
    heat_stream_lookup = {stream.stream_id: stream for stream in all_heat_streams}
    hot_streams = [stream for stream in all_heat_streams if stream.kind == "hot"]
    cold_streams = [stream for stream in all_heat_streams if stream.kind == "cold"]
    heat_stream_set = HeatStreamSet(
        route_id=utility_network_decision.route_id,
        hot_streams=hot_streams,
        cold_streams=cold_streams,
        pinch_temp_c=utility_network_decision.utility_target.pinch_temp_c,
        markdown="\n".join(
            [
                "| Stream | Kind | Source Unit | Supply (C) | Target (C) | Duty (kW) |",
                "| --- | --- | --- | --- | --- | --- |",
                *[
                    f"| {stream.stream_id} | {stream.kind} | {stream.source_unit_id} | {stream.supply_temp_c:.1f} | {stream.target_temp_c:.1f} | {stream.duty_kw:.3f} |"
                    for stream in all_heat_streams
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
        compatible_packet_candidates = _compatible_packet_candidates(topology, packet_candidates)
        candidates = [
            HeatMatchCandidate(
                candidate_id=f"{case.case_id}_{match.match_id}",
                hot_stream_id=match.hot_stream_id,
                cold_stream_id=match.cold_stream_id,
                topology=topology,
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
        selected_matches, selected_train_steps = _synthesize_selected_train(
            case.case_id,
            topology,
            case.heat_matches,
            compatible_packet_candidates,
            heat_stream_lookup,
            case.recovered_duty_kw,
        )
        network_cases.append(
            HeatNetworkCase(
                case_id=case.case_id,
                topology=topology,
                recovered_duty_kw=case.recovered_duty_kw,
                residual_hot_utility_kw=case.residual_hot_utility_kw,
                residual_cold_utility_kw=case.residual_cold_utility_kw,
                exchanger_count=len(selected_train_steps),
                match_candidates=candidates,
                selected_matches=selected_matches,
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
                ),
                citations=case.citations,
                assumptions=case.assumptions,
            )
        )
    selected_case = next(
        (case for case in network_cases if case.case_id == utility_network_decision.selected_case_id),
        network_cases[0] if network_cases else None,
    )
    architecture = HeatNetworkArchitecture(
        route_id=utility_network_decision.route_id,
        selected_case_id=selected_case.case_id if selected_case else utility_network_decision.selected_case_id,
        heat_stream_set=heat_stream_set,
        cases=network_cases,
        selected_train_steps=selected_case.selected_train_steps if selected_case else [],
        selected_package_items=[item for step in (selected_case.selected_train_steps if selected_case else []) for item in step.package_items],
        topology_summary=selected_case.topology if selected_case else "no architecture selected",
        markdown="\n".join(
            [
                f"Selected topology: {selected_case.topology if selected_case else 'n/a'}",
                "",
                f"Recovered duty: {selected_case.recovered_duty_kw:.3f} kW" if selected_case else "Recovered duty: n/a",
                f"Residual hot utility: {selected_case.residual_hot_utility_kw:.3f} kW" if selected_case else "Residual hot utility: n/a",
                f"Packet-level thermal candidates: {len(packet_candidates)}" if energy_balance is not None else "",
                f"Selected exchanger train steps: {len(selected_case.selected_train_steps)}" if selected_case else "Selected exchanger train steps: 0",
                f"Selected package items: {sum(len(step.package_items) for step in (selected_case.selected_train_steps if selected_case else []))}",
                *[
                    f"- {step.exchanger_id}: {step.service} via {step.medium}, {step.recovered_duty_kw:.3f} kW"
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
            f"Recoverable duty target: {utility_network_decision.utility_target.recoverable_duty_kw:.3f} kW",
            f"Selected annual utility cost: INR {utility_network_decision.selected_annual_utility_cost_inr:,.2f}/y",
            f"Thermal packet count: {len(energy_balance.unit_thermal_packets)}" if energy_balance is not None else "",
            f"Packet-derived exchanger candidates: {len(packet_candidates)}" if packet_candidates else "",
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
