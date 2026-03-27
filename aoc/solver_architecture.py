from __future__ import annotations

from collections import defaultdict

from aoc.models import (
    ConvergenceSummary,
    EnergyBalance,
    FlowsheetCase,
    FlowsheetGraph,
    RecycleLoop,
    SeparationSpec,
    SolveResult,
    StreamSpec,
    StreamTable,
    UnitSpec,
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


def build_flowsheet_case(route_id: str, operating_mode: str, stream_table: StreamTable, flowsheet_graph: FlowsheetGraph) -> FlowsheetCase:
    stream_specs: list[StreamSpec] = []
    incoming_by_unit: defaultdict[str, list[str]] = defaultdict(list)
    outgoing_by_unit: defaultdict[str, list[str]] = defaultdict(list)
    unit_packet_index = {packet.unit_id: packet for packet in stream_table.unit_operation_packets}
    unit_model_index = {model.unit_id: model for model in flowsheet_graph.unit_models}
    for stream in stream_table.streams:
        total_mass = sum(component.mass_flow_kg_hr for component in stream.components)
        total_molar = sum(component.molar_flow_kmol_hr for component in stream.components)
        stream_specs.append(
            StreamSpec(
                stream_id=stream.stream_id,
                source_unit_id=stream.source_unit_id,
                destination_unit_id=stream.destination_unit_id,
                phase_hint=stream.phase_hint,
                total_mass_flow_kg_hr=round(total_mass, 6),
                total_molar_flow_kmol_hr=round(total_molar, 6),
                component_names=[component.name for component in stream.components],
                citations=stream_table.citations,
                assumptions=stream_table.assumptions,
            )
        )
        if stream.destination_unit_id:
            incoming_by_unit[stream.destination_unit_id].append(stream.stream_id)
        if stream.source_unit_id:
            outgoing_by_unit[stream.source_unit_id].append(stream.stream_id)
    active_nodes = [
        node
        for node in flowsheet_graph.nodes
        if unit_packet_index.get(node.node_id) is not None
        or incoming_by_unit.get(node.node_id)
        or outgoing_by_unit.get(node.node_id)
    ]
    active_unit_ids = {node.node_id for node in active_nodes}

    unit_specs: list[UnitSpec] = []
    separation_specs: list[SeparationSpec] = []
    for node in active_nodes:
        packet = unit_packet_index.get(node.node_id)
        unit_model = unit_model_index.get(node.node_id)
        unit_specs.append(
            UnitSpec(
                unit_id=node.node_id,
                unit_type=node.unit_type,
                service=node.label,
                upstream_stream_ids=sorted(set(incoming_by_unit.get(node.node_id, []))),
                downstream_stream_ids=sorted(set(outgoing_by_unit.get(node.node_id, []))),
                closure_error_pct=packet.closure_error_pct if packet is not None else 0.0,
                closure_status=packet.status if packet is not None else flowsheet_graph.convergence_status,
                coverage_status=packet.coverage_status if packet is not None else "partial",
                missing_source_stream_ids=packet.missing_source_stream_ids if packet is not None else [],
                missing_destination_stream_ids=packet.missing_destination_stream_ids if packet is not None else [],
                unresolved_sensitivities=(
                    list(
                        dict.fromkeys(
                            (packet.unresolved_sensitivities if packet is not None else [])
                            + (unit_model.unresolved_sensitivities if unit_model is not None else [])
                            + flowsheet_graph.unresolved_sensitivities
                        )
                    )
                ),
                citations=flowsheet_graph.citations,
                assumptions=flowsheet_graph.assumptions,
            )
        )
    if stream_table.separation_packets:
        for packet in stream_table.separation_packets:
            separation_specs.append(
                SeparationSpec(
                    separation_id=packet.packet_id,
                    separation_family=packet.separation_family,
                    driving_force=packet.driving_force,
                    inlet_stream_ids=packet.inlet_stream_ids,
                    product_stream_ids=packet.product_stream_ids,
                    waste_stream_ids=packet.waste_stream_ids,
                    recycle_stream_ids=packet.recycle_stream_ids,
                    side_draw_stream_ids=packet.side_draw_stream_ids,
                    phase_split_spec_id=packet.phase_split_spec_id,
                    separator_performance_id=packet.separator_performance_id,
                    split_basis=packet.split_basis,
                    component_split_to_product=packet.component_split_to_product,
                    component_split_to_waste=packet.component_split_to_waste,
                    component_split_to_recycle=packet.component_split_to_recycle,
                    dominant_product_phase=packet.dominant_product_phase,
                    dominant_waste_phase=packet.dominant_waste_phase,
                    dominant_recycle_phase=packet.dominant_recycle_phase,
                    product_mass_fraction=packet.product_mass_fraction,
                    waste_mass_fraction=packet.waste_mass_fraction,
                    recycle_mass_fraction=packet.recycle_mass_fraction,
                    side_draw_mass_fraction=packet.side_draw_mass_fraction,
                    split_closure_pct=packet.split_closure_pct,
                    split_status=packet.split_status,
                    closure_error_pct=packet.closure_error_pct,
                    citations=packet.citations,
                    assumptions=packet.assumptions,
                )
            )
    else:
        for node in active_nodes:
            if node.unit_type not in SEPARATION_UNIT_TYPES:
                continue
            recycle_stream_ids = [
                stream_id
                for stream_id in outgoing_by_unit.get(node.node_id, [])
                if any(
                    stream.stream_id == stream_id and stream.destination_unit_id == "feed_prep"
                    for stream in stream_table.streams
                )
            ]
            waste_stream_ids = [
                stream_id
                for stream_id in outgoing_by_unit.get(node.node_id, [])
                if any(
                    stream.stream_id == stream_id and stream.destination_unit_id in {"waste_treatment", "battery_limits"}
                    for stream in stream_table.streams
                )
            ]
            product_stream_ids = [
                stream_id
                for stream_id in outgoing_by_unit.get(node.node_id, [])
                if stream_id not in recycle_stream_ids and stream_id not in waste_stream_ids
            ]
            separation_specs.append(
                SeparationSpec(
                    separation_id=f"{node.node_id}_separation",
                    separation_family=node.unit_type,
                    driving_force=(
                        "temperature/volatility"
                        if node.unit_type in {"flash", "distillation", "evaporation", "drying"}
                        else "solubility/phase split"
                    ),
                    inlet_stream_ids=sorted(set(incoming_by_unit.get(node.node_id, []))),
                    product_stream_ids=product_stream_ids,
                    waste_stream_ids=waste_stream_ids,
                    recycle_stream_ids=recycle_stream_ids,
                    citations=flowsheet_graph.citations,
                    assumptions=flowsheet_graph.assumptions,
                )
            )

    recycle_loops = []
    convergence_summaries: list[ConvergenceSummary] = []
    if stream_table.recycle_packets:
        for packet in stream_table.recycle_packets:
            recycle_loops.append(
                RecycleLoop(
                    loop_id=packet.loop_id,
                    recycle_source_unit_id=packet.recycle_source_unit_id,
                    recycle_stream_ids=sorted(set(packet.recycle_stream_ids)),
                    purge_stream_ids=sorted(set(packet.purge_stream_ids)),
                    component_convergence_error_pct=packet.component_convergence_error_pct,
                    purge_policy_by_family=packet.purge_policy_by_family,
                    impurity_family_components=packet.impurity_family_components,
                    convergence_summary_id=packet.convergence_summary_id,
                    convergence_status=packet.convergence_status,
                    closure_error_pct=packet.closure_error_pct,
                    max_iterations=packet.max_iterations,
                    citations=packet.citations,
                    assumptions=packet.assumptions,
                )
            )
    else:
        recycle_stream_ids = [
            stream.stream_id
            for stream in stream_table.streams
            if stream.destination_unit_id == "feed_prep"
        ]
        purge_stream_ids = [
            stream.stream_id
            for stream in stream_table.streams
            if "purge" in stream.description.lower() or stream.destination_unit_id == "waste_treatment"
        ]
        if recycle_stream_ids or purge_stream_ids:
            loop_id = f"{route_id}_main_recycle"
            recycle_loops.append(
                RecycleLoop(
                    loop_id=loop_id,
                    recycle_stream_ids=sorted(set(recycle_stream_ids)),
                    purge_stream_ids=sorted(set(purge_stream_ids)),
                    convergence_status="converged" if stream_table.closure_error_pct <= 2.0 else "estimated",
                    closure_error_pct=stream_table.closure_error_pct,
                    citations=stream_table.citations,
                    assumptions=stream_table.assumptions,
                )
            )
            convergence_summaries.append(
                ConvergenceSummary(
                    summary_id=f"{loop_id}_summary",
                    loop_id=loop_id,
                    recycle_stream_ids=sorted(set(recycle_stream_ids)),
                    purge_stream_ids=sorted(set(purge_stream_ids)),
                    component_count=0,
                    max_component_error_pct=0.0,
                    mean_component_error_pct=0.0,
                    max_iterations=0,
                    purge_policy_by_family={"mixed_impurities": 0.0},
                    impurity_family_components={},
                    convergence_status="converged" if stream_table.closure_error_pct <= 2.0 else "estimated",
                    notes=["Fallback recycle summary generated from stream-table connectivity."],
                    citations=stream_table.citations,
                    assumptions=stream_table.assumptions,
                )
            )
    if stream_table.convergence_summaries:
        convergence_summaries = list(stream_table.convergence_summaries)

    markdown_lines = [
        "| Unit | Type | Inlet Streams | Outlet Streams | Closure Error (%) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for unit in unit_specs:
        markdown_lines.append(
            f"| {unit.unit_id} | {unit.unit_type} | {', '.join(unit.upstream_stream_ids) or '-'} | {', '.join(unit.downstream_stream_ids) or '-'} | {unit.closure_error_pct:.3f} |"
        )
    return FlowsheetCase(
        case_id=f"{route_id}_flowsheet_case",
        route_id=route_id,
        operating_mode=operating_mode,
        units=unit_specs,
        streams=stream_specs,
        composition_states=[state for state in stream_table.composition_states if state.unit_id in active_unit_ids],
        composition_closures=[closure for closure in stream_table.composition_closures if closure.unit_id in active_unit_ids],
        separations=separation_specs,
        recycle_loops=recycle_loops,
        convergence_summaries=convergence_summaries,
        unit_operation_packets=stream_table.unit_operation_packets,
        markdown="\n".join(markdown_lines),
        citations=sorted(set(stream_table.citations + flowsheet_graph.citations)),
        assumptions=stream_table.assumptions + flowsheet_graph.assumptions,
    )


def build_solve_result(flowsheet_case: FlowsheetCase, stream_table: StreamTable, energy_balance: EnergyBalance) -> SolveResult:
    stream_index = {stream.stream_id: stream for stream in flowsheet_case.streams}
    packet_index = {packet.unit_id: packet for packet in flowsheet_case.unit_operation_packets}
    thermal_packet_index = {packet.unit_id: packet for packet in energy_balance.unit_thermal_packets}
    unitwise_closure: dict[str, float] = {}
    unitwise_status: dict[str, str] = {}
    unitwise_coverage_status: dict[str, str] = {}
    unitwise_blockers: dict[str, list[str]] = {}
    unitwise_unresolved_sensitivities: dict[str, list[str]] = {}
    composition_status: dict[str, str] = {}
    separation_status: dict[str, str] = {}
    recycle_status: dict[str, str] = {}
    convergence_summary_index = {summary.loop_id: summary for summary in flowsheet_case.convergence_summaries}
    composition_closure_index = {closure.unit_id: closure for closure in flowsheet_case.composition_closures}
    critic_messages: list[str] = []
    for unit in flowsheet_case.units:
        blockers: list[str] = []
        packet = packet_index.get(unit.unit_id)
        if packet is not None:
            unitwise_closure[unit.unit_id] = round(packet.closure_error_pct, 6)
            unitwise_status[unit.unit_id] = packet.status
            unitwise_coverage_status[unit.unit_id] = packet.coverage_status
            if packet.status == "blocked":
                blockers.append(f"Unit '{unit.unit_id}' is blocked with closure {packet.closure_error_pct:.3f}% or missing inlet/outlet coverage.")
            elif packet.closure_error_pct > 2.0:
                critic_messages.append(f"Unit '{unit.unit_id}' closure is {packet.closure_error_pct:.3f}%, which is outside the converged range.")
            if packet.missing_source_stream_ids:
                blockers.append(
                    f"Unit '{unit.unit_id}' has inlet streams without upstream source references: {', '.join(packet.missing_source_stream_ids)}."
                )
            if packet.missing_destination_stream_ids:
                blockers.append(
                    f"Unit '{unit.unit_id}' has outlet streams without downstream destination references: {', '.join(packet.missing_destination_stream_ids)}."
                )
        else:
            mass_in = sum(stream_index[stream_id].total_mass_flow_kg_hr for stream_id in unit.upstream_stream_ids if stream_id in stream_index)
            mass_out = sum(stream_index[stream_id].total_mass_flow_kg_hr for stream_id in unit.downstream_stream_ids if stream_id in stream_index)
            unitwise_coverage_status[unit.unit_id] = unit.coverage_status
            if unit.unit_type in {"storage", "waste_handling"}:
                unitwise_closure[unit.unit_id] = 0.0
                unitwise_status[unit.unit_id] = "converged"
            elif unit.unit_type == "recycle":
                unitwise_closure[unit.unit_id] = 0.0 if (mass_in > 0.0 or mass_out > 0.0) else 0.0
                unitwise_status[unit.unit_id] = "converged" if (mass_in > 0.0 or mass_out > 0.0) else "estimated"
            elif mass_in <= 0.0 and mass_out <= 0.0:
                unitwise_closure[unit.unit_id] = 0.0
                unitwise_status[unit.unit_id] = "estimated"
                blockers.append(f"Unit '{unit.unit_id}' has no solved inlet or outlet streams in the flowsheet case.")
            else:
                closure = round(abs(mass_out - mass_in) / max(mass_in, mass_out, 1.0) * 100.0, 6)
                unitwise_closure[unit.unit_id] = closure
                unitwise_status[unit.unit_id] = "converged" if closure <= 2.0 else "estimated" if closure <= 5.0 else "blocked"

        thermal_packet = thermal_packet_index.get(unit.unit_id)
        matching_duty = next((duty for duty in energy_balance.duties if duty.unit_id == unit.unit_id), None)
        if matching_duty is not None and thermal_packet is None:
            critic_messages.append(f"Unit '{unit.unit_id}' has an explicit duty row but no unit thermal packet.")
        if thermal_packet is not None:
            if thermal_packet.heating_kw > 0.0 and thermal_packet.cold_target_temp_c <= thermal_packet.cold_supply_temp_c:
                blockers.append(f"Unit '{unit.unit_id}' thermal packet has no usable cold-side temperature rise.")
            if thermal_packet.cooling_kw > 0.0 and thermal_packet.hot_supply_temp_c <= thermal_packet.hot_target_temp_c:
                blockers.append(f"Unit '{unit.unit_id}' thermal packet has no usable hot-side temperature drop.")
        if unit.unresolved_sensitivities:
            unitwise_unresolved_sensitivities[unit.unit_id] = sorted(dict.fromkeys(unit.unresolved_sensitivities))
        if blockers:
            unitwise_blockers[unit.unit_id] = blockers
            critic_messages.extend(blockers)
        composition_closure = composition_closure_index.get(unit.unit_id)
        if composition_closure is not None:
            composition_status[unit.unit_id] = composition_closure.closure_status
            if composition_closure.closure_status == "blocked":
                critic_messages.append(f"Unit '{unit.unit_id}' has blocked composition closure.")
            elif composition_closure.closure_status == "estimated":
                critic_messages.append(f"Unit '{unit.unit_id}' retains estimated composition closure.")
        elif unit.unit_type in {"storage", "waste_handling", "recycle"}:
            composition_status[unit.unit_id] = "converged"
        else:
            composition_status[unit.unit_id] = "blocked"
            critic_messages.append(f"Unit '{unit.unit_id}' has no composition-closure artifact.")

    unresolved = sorted(
        {
            sensitivity
            for unit in flowsheet_case.units
            for sensitivity in unit.unresolved_sensitivities
        }
    )
    for separation in flowsheet_case.separations:
        split_status = separation.split_status
        if not separation.inlet_stream_ids:
            critic_messages.append(f"Separation '{separation.separation_id}' has no inlet stream ids.")
            split_status = "blocked"
        if not (separation.product_stream_ids or separation.recycle_stream_ids or separation.waste_stream_ids or separation.side_draw_stream_ids):
            critic_messages.append(f"Separation '{separation.separation_id}' has no resolved outlet split streams.")
            split_status = "blocked"
        if separation.closure_error_pct > 5.0:
            critic_messages.append(f"Separation '{separation.separation_id}' closure is {separation.closure_error_pct:.3f}%, which is too high for design-basis lock.")
            split_status = "blocked"
        if separation.split_closure_pct > 25.0:
            critic_messages.append(
                f"Separation '{separation.separation_id}' split closure is {separation.split_closure_pct:.3f}%, which is too high for a defendable separator basis."
            )
            split_status = "blocked"
        for component_name in set(separation.component_split_to_product) | set(separation.component_split_to_waste) | set(separation.component_split_to_recycle):
            split_total = (
                separation.component_split_to_product.get(component_name, 0.0)
                + separation.component_split_to_waste.get(component_name, 0.0)
                + separation.component_split_to_recycle.get(component_name, 0.0)
            )
            if split_total > 1.10 or split_total < 0.75:
                critic_messages.append(
                    f"Separation '{separation.separation_id}' has weak component split closure for '{component_name}' with total split {split_total:.3f}."
                )
                split_status = "estimated" if split_status == "converged" else split_status
        separation_status[separation.separation_id] = split_status if split_status != "converged" or separation.closure_error_pct <= 2.0 else "estimated"
    stream_ids = {stream.stream_id for stream in flowsheet_case.streams}
    for loop in flowsheet_case.recycle_loops:
        loop_status = loop.convergence_status
        missing_recycle = [stream_id for stream_id in loop.recycle_stream_ids if stream_id not in stream_ids]
        missing_purge = [stream_id for stream_id in loop.purge_stream_ids if stream_id not in stream_ids]
        if missing_recycle or missing_purge:
            critic_messages.append(
                f"Recycle loop '{loop.loop_id}' references missing streams: recycle={missing_recycle or ['-']}, purge={missing_purge or ['-']}."
            )
            loop_status = "blocked"
        if loop.convergence_status == "blocked":
            critic_messages.append(f"Recycle loop '{loop.loop_id}' is blocked.")
        elif loop.convergence_status == "estimated":
            critic_messages.append(f"Recycle loop '{loop.loop_id}' remains estimated and needs review before freezing detailed design.")
        max_component_error = max(loop.component_convergence_error_pct.values(), default=0.0)
        if max_component_error > 95.0:
            critic_messages.append(f"Recycle loop '{loop.loop_id}' has component convergence error {max_component_error:.3f}%, which is too high.")
            loop_status = "blocked"
        elif max_component_error > 10.0 and loop_status == "converged":
            critic_messages.append(f"Recycle loop '{loop.loop_id}' has component convergence error {max_component_error:.3f}% and remains estimated.")
            loop_status = "estimated"
        summary = convergence_summary_index.get(loop.loop_id)
        if summary is not None:
            if not summary.purge_policy_by_family:
                critic_messages.append(f"Recycle loop '{loop.loop_id}' has no explicit purge policy by impurity family.")
                loop_status = "blocked"
            if summary.blocked_components:
                critic_messages.append(
                    f"Recycle loop '{loop.loop_id}' has blocked components in the convergence summary: {', '.join(summary.blocked_components[:4])}."
                )
                loop_status = "blocked"
            elif summary.estimated_components and loop_status == "converged":
                critic_messages.append(
                    f"Recycle loop '{loop.loop_id}' retains estimated convergence for components: {', '.join(summary.estimated_components[:4])}."
                )
                loop_status = "estimated"
        recycle_status[loop.loop_id] = loop_status
    markdown_lines = [
        "| Unit | Closure Error (%) | Status | Heating Duty (kW) | Cooling Duty (kW) |",
        "| --- | --- | --- | --- | --- |",
    ]
    energy_map = {duty.unit_id: duty for duty in energy_balance.duties}
    for unit in flowsheet_case.units:
        duty = energy_map.get(unit.unit_id)
        markdown_lines.append(
            f"| {unit.unit_id} | {unitwise_closure.get(unit.unit_id, 0.0):.6f} | {unitwise_status.get(unit.unit_id, 'estimated')} | {duty.heating_kw if duty else 0.0:.3f} | {duty.cooling_kw if duty else 0.0:.3f} |"
        )
    max_closure = max(unitwise_closure.values(), default=0.0)
    if (
        any(status == "blocked" for status in unitwise_status.values())
        or any(status == "blocked" for status in composition_status.values())
        or any(loop.convergence_status == "blocked" for loop in flowsheet_case.recycle_loops)
    ):
        status = "blocked"
    elif stream_table.closure_error_pct <= 2.0 and max_closure <= 2.0 and not critic_messages:
        status = "converged"
    elif stream_table.closure_error_pct <= 5.0:
        status = "estimated"
    else:
        status = "blocked"
    return SolveResult(
        case_id=flowsheet_case.case_id,
        convergence_status=status,
        overall_closure_error_pct=stream_table.closure_error_pct,
        unitwise_closure=unitwise_closure,
        unitwise_status=unitwise_status,
        unitwise_coverage_status=unitwise_coverage_status,
        unitwise_blockers=unitwise_blockers,
        unitwise_unresolved_sensitivities=unitwise_unresolved_sensitivities,
        composition_status=composition_status,
        separation_status=separation_status,
        recycle_status=recycle_status,
        convergence_summaries=flowsheet_case.convergence_summaries,
        unresolved_sensitivities=unresolved,
        critic_messages=critic_messages,
        markdown="\n".join(markdown_lines),
        citations=sorted(set(flowsheet_case.citations + stream_table.citations + energy_balance.citations)),
        assumptions=flowsheet_case.assumptions + stream_table.assumptions + energy_balance.assumptions,
    )
