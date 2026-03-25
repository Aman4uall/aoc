from __future__ import annotations

from aoc.models import (
    EnergyBalance,
    HeatExchangerTrainStep,
    HeatMatch,
    HeatMatchCandidate,
    HeatNetworkArchitecture,
    HeatNetworkCase,
    HeatStream,
    HeatStreamSet,
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

    train_steps = [
        _train_step(case_id, index, topology, match, heat_stream_lookup)
        for index, match in enumerate(selected_matches, start=1)
    ]
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
        topology_summary=selected_case.topology if selected_case else "no architecture selected",
        markdown="\n".join(
            [
                f"Selected topology: {selected_case.topology if selected_case else 'n/a'}",
                "",
                f"Recovered duty: {selected_case.recovered_duty_kw:.3f} kW" if selected_case else "Recovered duty: n/a",
                f"Residual hot utility: {selected_case.residual_hot_utility_kw:.3f} kW" if selected_case else "Residual hot utility: n/a",
                f"Packet-level thermal candidates: {len(packet_candidates)}" if energy_balance is not None else "",
                f"Selected exchanger train steps: {len(selected_case.selected_train_steps)}" if selected_case else "Selected exchanger train steps: 0",
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
