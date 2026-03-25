from __future__ import annotations

from aoc.models import (
    AlternativeOption,
    CalcTrace,
    ControlArchitectureDecision,
    ControlLoop,
    ControlPlanArtifact,
    DecisionCriterion,
    DecisionRecord,
    EquipmentListArtifact,
    FlowsheetGraph,
    FlowsheetNode,
    HazopNode,
    HazopNodeRegister,
    LayoutDecisionArtifact,
    ProcessNarrativeArtifact,
    ReactionSystem,
    RouteOption,
    ScenarioStability,
    StreamTable,
    UtilitySummaryArtifact,
    UnitOperationModel,
)


def _separation_unit_type(route: RouteOption) -> str:
    text = " ".join(route.separations).lower()
    if "absor" in text or "strip" in text:
        return "absorption"
    if "extract" in text:
        return "extraction"
    if "crystal" in text or "filter" in text:
        return "crystallization"
    if "distill" in text or "vacuum" in text:
        return "distillation"
    if "dry" in text:
        return "drying"
    if "flash" in text:
        return "flash"
    return "separation"


def _unit_metadata(unit_id: str, separation_type: str) -> tuple[str, str]:
    if unit_id == "feed_prep":
        return "feed_preparation", "Feed preparation"
    if unit_id == "reactor":
        return "reactor", "Reaction zone"
    if unit_id == "primary_flash":
        return "flash", "Primary flash and purge recovery"
    if unit_id == "primary_separation":
        return separation_type if separation_type != "separation" else "separation", "Primary separation"
    if unit_id == "concentration":
        if separation_type == "crystallization":
            return "crystallization", "Crystallization and mother-liquor split"
        return "evaporation", "Water removal and concentration"
    if unit_id == "purification":
        if separation_type == "extraction":
            return "extraction", "Purification train"
        return "distillation", "Purification train"
    if unit_id == "filtration":
        return "filtration", "Filtration and solids split"
    if unit_id == "drying":
        return "drying", "Drying and finishing"
    if unit_id == "regeneration":
        return "stripping", "Regeneration and recycle"
    if unit_id == "recycle_recovery":
        return "recycle", "Recycle recovery"
    if unit_id == "storage":
        return "storage", "Product storage"
    if unit_id == "waste_treatment":
        return "waste_handling", "Waste treatment"
    return "unit_operation", unit_id.replace("_", " ").title()


def build_flowsheet_graph(
    route: RouteOption,
    stream_table: StreamTable,
    reaction_system: ReactionSystem,
    process_narrative: ProcessNarrativeArtifact,
    operating_mode: str,
) -> FlowsheetGraph:
    stream_ids = [stream.stream_id for stream in stream_table.streams]
    separation_type = _separation_unit_type(route)
    ordered_unit_ids: list[str] = []
    for stream in stream_table.streams:
        for unit_id in (stream.source_unit_id, stream.destination_unit_id):
            if not unit_id or unit_id == "battery_limits":
                continue
            if unit_id not in ordered_unit_ids:
                ordered_unit_ids.append(unit_id)

    nodes: list[FlowsheetNode] = []
    for unit_id in ordered_unit_ids:
        unit_type, label = _unit_metadata(unit_id, separation_type)
        upstream_nodes = []
        downstream_nodes = []
        representative_stream_ids = []
        for stream in stream_table.streams:
            if stream.destination_unit_id == unit_id and stream.source_unit_id and stream.source_unit_id != "battery_limits":
                if stream.source_unit_id not in upstream_nodes:
                    upstream_nodes.append(stream.source_unit_id)
                representative_stream_ids.append(stream.stream_id)
            if stream.source_unit_id == unit_id and stream.destination_unit_id:
                if stream.destination_unit_id not in downstream_nodes:
                    downstream_nodes.append(stream.destination_unit_id)
                representative_stream_ids.append(stream.stream_id)
        nodes.append(
            FlowsheetNode(
                node_id=unit_id,
                unit_type=unit_type,
                label=label,
                upstream_nodes=upstream_nodes,
                downstream_nodes=downstream_nodes,
                representative_stream_ids=sorted(dict.fromkeys(representative_stream_ids)),
            )
        )
    unit_models = [
        UnitOperationModel(
            unit_id=node.node_id,
            unit_type=node.unit_type,
            service=node.label,
            formula_traces=[
                CalcTrace(
                    trace_id=f"{node.node_id}_basis",
                    title=f"{node.label} basis",
                    formula="seeded unit-op basis",
                    substitutions={"operating_mode": operating_mode, "route_id": route.route_id},
                    result="configured",
                    notes="Generic flowsheet graph seeded from the selected route and stream table.",
                )
            ],
            convergence_status="converged" if stream_table.closure_error_pct <= 2.0 else "estimated",
            unresolved_sensitivities=[
                value.name for value in reaction_system.value_records if value.blocking
            ],
            citations=sorted(set(route.citations + stream_table.citations)),
            assumptions=route.assumptions + reaction_system.assumptions,
        )
        for node in nodes
    ]
    markdown = "\n".join(
        [
            "| Node | Unit Type | Upstream | Downstream | Representative Streams |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {node.node_id} | {node.unit_type} | {', '.join(node.upstream_nodes) or '-'} | {', '.join(node.downstream_nodes) or '-'} | {', '.join(node.representative_stream_ids) or '-'} |"
                for node in nodes
            ],
        ]
    )
    return FlowsheetGraph(
        graph_id=f"{route.route_id}_flowsheet",
        route_id=route.route_id,
        operating_mode=operating_mode,
        nodes=nodes,
        unit_models=unit_models,
        stream_ids=stream_ids,
        convergence_status="converged" if stream_table.closure_error_pct <= 2.0 else "estimated",
        unresolved_sensitivities=sorted({value.name for value in reaction_system.value_records if value.blocking}),
        markdown=markdown,
        citations=sorted(set(route.citations + stream_table.citations + process_narrative.citations)),
        assumptions=route.assumptions + reaction_system.assumptions + process_narrative.assumptions,
    )


def build_control_architecture_decision(
    route: RouteOption,
    equipment: EquipmentListArtifact,
    utility_summary_json: str,
    control_plan: ControlPlanArtifact,
    flowsheet_graph: FlowsheetGraph,
) -> ControlArchitectureDecision:
    critical_units = []
    for item in equipment.items:
        equipment_type = item.equipment_type.lower()
        if any(token in equipment_type for token in {"reactor", "column", "storage", "tank"}):
            critical_units.append(item.equipment_id)
    alternatives = [
        {
            "candidate_id": "basic_regulatory",
            "description": "Basic regulatory loops with alarms",
            "score": 62.0,
            "feasible": True,
            "rejected": ["Too weak for high-hazard integrated service."] if any(h.severity == "high" for h in route.hazards) else [],
        },
        {
            "candidate_id": "cascade_override",
            "description": "Cascade temperature/pressure control with override protection",
            "score": 84.0,
            "feasible": True,
            "rejected": [],
        },
        {
            "candidate_id": "sis_augmented",
            "description": "Regulatory control plus SIS/interlocks on critical nodes",
            "score": 92.0 if any(h.severity == "high" for h in route.hazards) else 78.0,
            "feasible": True,
            "rejected": [],
        },
    ]
    selected = max(alternatives, key=lambda item: item["score"])
    decision = DecisionRecord(
        decision_id="control_architecture",
        context=f"Control architecture selection from flowsheet critical units. Utility summary basis length={len(utility_summary_json)}.",
        criteria=[
            DecisionCriterion(name="Hazard coverage", weight=0.4, justification="High-hazard routes require stronger protective layers."),
            DecisionCriterion(name="Operability", weight=0.35, justification="Stable steady-state control is required for process and utility integration."),
            DecisionCriterion(name="Implementation complexity", weight=0.25, justification="The control philosophy should remain feasibility-study realistic."),
        ],
        alternatives=[
            AlternativeOption(
                candidate_id=item["candidate_id"],
                candidate_type="control_architecture",
                description=item["description"],
                rejected_reasons=item["rejected"],
                total_score=item["score"],
                score_breakdown={"overall": item["score"]},
                feasible=item["feasible"],
            )
            for item in alternatives
        ],
        selected_candidate_id=selected["candidate_id"],
        selected_summary=f"{selected['description']} selected for the current flowsheet and hazard profile.",
        confidence=0.78,
        scenario_stability=ScenarioStability.STABLE,
        approval_required=selected["candidate_id"] == "sis_augmented" and len(critical_units) > 3,
        citations=sorted(set(route.citations + control_plan.citations + flowsheet_graph.citations)),
        assumptions=control_plan.assumptions + flowsheet_graph.assumptions,
    )
    markdown = (
        f"Selected control architecture: {selected['description']}.\n\n"
        f"Critical units: {', '.join(critical_units) or 'none'}.\n\n"
        f"Existing control loops captured: {len(control_plan.control_loops)}."
    )
    return ControlArchitectureDecision(
        decision=decision,
        critical_units=critical_units,
        markdown=markdown,
        citations=decision.citations,
        assumptions=decision.assumptions,
    )


def build_control_plan_from_flowsheet(
    route: RouteOption,
    equipment: EquipmentListArtifact,
    utility_summary: UtilitySummaryArtifact,
    flowsheet_graph: FlowsheetGraph,
) -> ControlPlanArtifact:
    loops: list[ControlLoop] = []
    for item in equipment.items:
        lowered = item.equipment_type.lower()
        if "reactor" in lowered:
            loops.append(
                ControlLoop(
                    control_id=f"TIC-{item.equipment_id}",
                    controlled_variable=f"{item.service} temperature",
                    manipulated_variable="Cooling or heating duty",
                    sensor="Temperature transmitter",
                    actuator="Control valve",
                    notes="Protects conversion and selectivity while limiting thermal upset.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
            loops.append(
                ControlLoop(
                    control_id=f"PIC-{item.equipment_id}",
                    controlled_variable=f"{item.service} pressure",
                    manipulated_variable="Back-pressure control",
                    sensor="Pressure transmitter",
                    actuator="Control valve",
                    notes="Maintains design pressure envelope.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
        elif "process unit" in lowered or "column" in lowered:
            loops.append(
                ControlLoop(
                    control_id=f"LIC-{item.equipment_id}",
                    controlled_variable=f"{item.service} level",
                    manipulated_variable="Bottoms withdrawal",
                    sensor="Level transmitter",
                    actuator="Control valve",
                    notes="Protects internals and downstream product quality.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
        elif "storage" in lowered:
            loops.append(
                ControlLoop(
                    control_id=f"LIC-{item.equipment_id}",
                    controlled_variable=f"{item.service} level",
                    manipulated_variable="Dispatch pump permissive",
                    sensor="Level transmitter",
                    actuator="Pump trip",
                    notes="Prevents overflow and dry running.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
    if not loops:
        loops.append(
            ControlLoop(
                control_id="FIC-101",
                controlled_variable="Feed flow",
                manipulated_variable="Feed pump speed",
                sensor="Flow transmitter",
                actuator="VFD",
                notes="Generic feed stabilization loop.",
                citations=route.citations,
                assumptions=route.assumptions,
            )
        )
    utility_count = len(utility_summary.items)
    markdown = (
        f"The deterministic control plan derives {len(loops)} loops from {len(equipment.items)} major equipment items and {utility_count} utility services. "
        "Loops are attached to thermal, pressure, level, and feed-stability risks rather than generated as generic instrumentation text."
    )
    return ControlPlanArtifact(
        control_loops=loops,
        markdown=markdown,
        citations=sorted(set(route.citations + utility_summary.citations + flowsheet_graph.citations)),
        assumptions=route.assumptions + utility_summary.assumptions + flowsheet_graph.assumptions,
    )


def build_hazop_node_register(
    route: RouteOption,
    equipment: EquipmentListArtifact,
    flowsheet_graph: FlowsheetGraph,
    control_plan: ControlPlanArtifact,
) -> HazopNodeRegister:
    nodes: list[HazopNode] = []
    control_ids = [loop.control_id for loop in control_plan.control_loops]
    for item in equipment.items:
        lowered = item.equipment_type.lower()
        if "reactor" in lowered:
            nodes.append(
                HazopNode(
                    node_id=item.equipment_id,
                    parameter="Temperature",
                    guide_word="More",
                    causes=["Cooling failure", "Excess reactant feed"],
                    consequences=["Runaway tendency", "Selectivity loss"],
                    safeguards=control_ids[:2] or ["High-temperature alarm"],
                    recommendation="Add high-high temperature trip and emergency feed isolation.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
        elif "column" in lowered or "distillation" in lowered:
            nodes.append(
                HazopNode(
                    node_id=item.equipment_id,
                    parameter="Pressure",
                    guide_word="Less",
                    causes=["Vacuum overshoot", "Condenser instability"],
                    consequences=["Air ingress", "Column instability"],
                    safeguards=control_ids[:2] or ["Pressure alarm"],
                    recommendation="Protect low-pressure operation and verify oxygen ingress response.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
        elif "storage" in lowered or "tank" in lowered:
            nodes.append(
                HazopNode(
                    node_id=item.equipment_id,
                    parameter="Level",
                    guide_word="More",
                    causes=["Blocked outlet", "Dispatch mismatch"],
                    consequences=["Overflow", "Containment loss"],
                    safeguards=control_ids[:1] or ["High-level alarm"],
                    recommendation="Provide level interlocks and overflow routing checks.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
    if not nodes:
        for node in flowsheet_graph.nodes:
            nodes.append(
                HazopNode(
                    node_id=node.node_id,
                    parameter="Flow",
                    guide_word="No",
                    causes=["Pump trip", "Valve isolation"],
                    consequences=["Starved downstream section", "Off-spec operation"],
                    safeguards=["Flow alarm"],
                    recommendation="Confirm flow permissives across the generic flowsheet.",
                    citations=route.citations,
                    assumptions=route.assumptions,
                )
            )
    coverage_summary = f"{len(nodes)} HAZOP nodes derived from the selected flowsheet and equipment list."
    markdown = "### HAZOP Node Register\n\n" + "\n".join(
        [
            "| Node | Parameter | Guide Word | Causes | Consequences | Safeguards | Recommendation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {node.node_id} | {node.parameter} | {node.guide_word} | {'; '.join(node.causes)} | {'; '.join(node.consequences)} | {'; '.join(node.safeguards)} | {node.recommendation} |"
                for node in nodes
            ],
        ]
    )
    return HazopNodeRegister(
        nodes=nodes,
        coverage_summary=coverage_summary,
        markdown=markdown,
        citations=sorted(set(route.citations + control_plan.citations + flowsheet_graph.citations)),
        assumptions=route.assumptions + control_plan.assumptions + flowsheet_graph.assumptions,
    )


def build_layout_decision(
    site_name: str,
    equipment: EquipmentListArtifact,
    utility_summary: UtilitySummaryArtifact,
    flowsheet_graph: FlowsheetGraph,
    layout_choice: DecisionRecord,
) -> LayoutDecisionArtifact:
    selected = next((item for item in layout_choice.alternatives if item.candidate_id == layout_choice.selected_candidate_id), None)
    winning_basis = selected.description if selected else "Layout basis unavailable"
    markdown = (
        f"Selected layout basis: {winning_basis}. "
        f"The scored winner is tied to {site_name}, {len(equipment.items)} major equipment items, {len(utility_summary.items)} utility services, "
        f"and {len(flowsheet_graph.nodes)} solved flowsheet nodes. The layout narrative therefore follows the scored arrangement rather than freewriting a generic plot plan."
    )
    return LayoutDecisionArtifact(
        decision=layout_choice,
        winning_layout_basis=winning_basis,
        markdown=markdown,
        citations=sorted(set(layout_choice.citations + equipment.citations + utility_summary.citations + flowsheet_graph.citations)),
        assumptions=layout_choice.assumptions + equipment.assumptions + utility_summary.assumptions + flowsheet_graph.assumptions,
    )
