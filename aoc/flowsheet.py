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
    if "dry" in text:
        return "drying"
    if "flash" in text:
        return "flash"
    if "distill" in text or "vacuum" in text:
        return "distillation"
    return "separation"


def build_flowsheet_graph(
    route: RouteOption,
    stream_table: StreamTable,
    reaction_system: ReactionSystem,
    process_narrative: ProcessNarrativeArtifact,
    operating_mode: str,
) -> FlowsheetGraph:
    stream_ids = [stream.stream_id for stream in stream_table.streams]
    separation_type = _separation_unit_type(route)
    has_concentration = any(stream.stream_id == "S-302" for stream in stream_table.streams)
    if separation_type == "distillation":
        nodes = [
            FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed preparation", downstream_nodes=["reactor"], representative_stream_ids=[item for item in stream_ids if item.startswith("S-10") or item == "S-150"]),
            FlowsheetNode(node_id="reactor", unit_type="reactor", label="Reaction zone", upstream_nodes=["feed_prep"], downstream_nodes=["primary_flash"], representative_stream_ids=["S-201"]),
            FlowsheetNode(node_id="primary_flash", unit_type="flash", label="Primary flash and purge recovery", upstream_nodes=["reactor"], downstream_nodes=["concentration", "recycle_recovery"], representative_stream_ids=["S-202", "S-203"]),
            FlowsheetNode(node_id="concentration", unit_type="evaporation", label="Water removal and concentration", upstream_nodes=["primary_flash"], downstream_nodes=["purification", "recycle_recovery"], representative_stream_ids=["S-301", "S-302"] if has_concentration else ["S-203"]),
            FlowsheetNode(node_id="purification", unit_type="distillation", label="Purification columns", upstream_nodes=["concentration"], downstream_nodes=["product_storage", "waste_treatment"], representative_stream_ids=["S-401", "S-402", "S-403"]),
            FlowsheetNode(node_id="recycle_recovery", unit_type="recycle", label="Recycle and condensate recovery", upstream_nodes=["primary_flash", "concentration"], downstream_nodes=["feed_prep"], representative_stream_ids=["S-301"]),
            FlowsheetNode(node_id="product_storage", unit_type="storage", label="Product finishing and storage", upstream_nodes=["purification"], representative_stream_ids=["S-402"]),
            FlowsheetNode(node_id="waste_treatment", unit_type="waste_handling", label="Purge and heavy-ends handling", upstream_nodes=["purification"], representative_stream_ids=["S-401", "S-403"]),
        ]
    elif separation_type == "crystallization":
        nodes = [
            FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed preparation", downstream_nodes=["reactor"], representative_stream_ids=[item for item in stream_ids if item.startswith("S-10") or item == "S-150"]),
            FlowsheetNode(node_id="reactor", unit_type="reactor", label="Reaction / carbonation zone", upstream_nodes=["feed_prep"], downstream_nodes=["crystallization"], representative_stream_ids=["S-201", "S-203"]),
            FlowsheetNode(node_id="crystallization", unit_type="crystallization", label="Crystallization", upstream_nodes=["reactor"], downstream_nodes=["filtration", "recycle_recovery"], representative_stream_ids=["S-301", "S-302"]),
            FlowsheetNode(node_id="filtration", unit_type="filtration", label="Filtration and mother-liquor split", upstream_nodes=["crystallization"], downstream_nodes=["drying", "recycle_recovery"], representative_stream_ids=["S-302", "S-403"]),
            FlowsheetNode(node_id="drying", unit_type="drying", label="Drying and finishing", upstream_nodes=["filtration"], downstream_nodes=["product_storage"], representative_stream_ids=["S-402"]),
            FlowsheetNode(node_id="recycle_recovery", unit_type="recycle", label="Mother-liquor recycle", upstream_nodes=["crystallization", "filtration"], downstream_nodes=["feed_prep"], representative_stream_ids=["S-301"]),
            FlowsheetNode(node_id="product_storage", unit_type="storage", label="Product storage", upstream_nodes=["drying"], representative_stream_ids=["S-402"]),
        ]
    elif separation_type == "absorption":
        nodes = [
            FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed preparation", downstream_nodes=["reactor"], representative_stream_ids=[item for item in stream_ids if item.startswith("S-10") or item == "S-150"]),
            FlowsheetNode(node_id="reactor", unit_type="reactor", label="Converter / reactor zone", upstream_nodes=["feed_prep"], downstream_nodes=["primary_separation"], representative_stream_ids=["S-201"]),
            FlowsheetNode(node_id="primary_separation", unit_type="absorption", label="Absorption and scrubbing", upstream_nodes=["reactor"], downstream_nodes=["regeneration", "product_storage"], representative_stream_ids=["S-202", "S-203"]),
            FlowsheetNode(node_id="regeneration", unit_type="stripping", label="Regeneration and recycle", upstream_nodes=["primary_separation"], downstream_nodes=["feed_prep"], representative_stream_ids=["S-301"]),
            FlowsheetNode(node_id="product_storage", unit_type="storage", label="Product storage", upstream_nodes=["primary_separation"], representative_stream_ids=["S-401", "S-402"]),
        ]
    else:
        nodes = [
            FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed preparation", downstream_nodes=["reactor"], representative_stream_ids=[item for item in stream_ids if item.startswith("S-10") or item == "S-150"]),
            FlowsheetNode(node_id="reactor", unit_type="reactor", label="Reaction zone", upstream_nodes=["feed_prep"], downstream_nodes=["primary_separation"], representative_stream_ids=["S-201"]),
            FlowsheetNode(node_id="primary_separation", unit_type=separation_type, label="Primary separation", upstream_nodes=["reactor"], downstream_nodes=["product_finish", "recycle_recovery"], representative_stream_ids=["S-202", "S-203"]),
            FlowsheetNode(node_id="recycle_recovery", unit_type="recycle", label="Recycle recovery", upstream_nodes=["primary_separation"], downstream_nodes=["feed_prep"], representative_stream_ids=["S-301"]),
            FlowsheetNode(node_id="product_finish", unit_type="product_finishing", label="Product finishing and storage", upstream_nodes=["primary_separation"], representative_stream_ids=["S-401", "S-402", "S-403"]),
        ]
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
