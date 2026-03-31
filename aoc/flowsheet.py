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
    FlowsheetBlueprintArtifact,
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
    flowsheet_blueprint: FlowsheetBlueprintArtifact | None = None,
) -> FlowsheetGraph:
    stream_ids = [stream.stream_id for stream in stream_table.streams]
    separation_type = _separation_unit_type(route)
    section_by_unit = {
        unit_id: section
        for section in stream_table.sections
        for unit_id in section.unit_ids
    }
    recycle_loops_by_source: dict[str, list[str]] = {}
    for packet in stream_table.recycle_packets:
        if packet.recycle_source_unit_id:
            recycle_loops_by_source.setdefault(packet.recycle_source_unit_id, []).append(packet.loop_id)
    blueprint_steps_by_anchor: dict[str, object] = {}
    blueprint_order: list[str] = []
    if flowsheet_blueprint is not None:
        for step in flowsheet_blueprint.steps:
            anchor = step.solver_anchor_unit_id or step.unit_id
            if not anchor:
                continue
            if anchor not in blueprint_steps_by_anchor:
                blueprint_steps_by_anchor[anchor] = step
            if anchor not in blueprint_order:
                blueprint_order.append(anchor)

    ordered_unit_ids: list[str] = []
    for unit_id in blueprint_order:
        if any(
            stream.source_unit_id == unit_id or stream.destination_unit_id == unit_id
            for stream in stream_table.streams
        ):
            ordered_unit_ids.append(unit_id)
    for stream in stream_table.streams:
        for unit_id in (stream.source_unit_id, stream.destination_unit_id):
            if not unit_id or unit_id == "battery_limits":
                continue
            if unit_id not in ordered_unit_ids:
                ordered_unit_ids.append(unit_id)

    nodes: list[FlowsheetNode] = []
    for unit_id in ordered_unit_ids:
        blueprint_step = blueprint_steps_by_anchor.get(unit_id)
        if blueprint_step is not None:
            unit_type = blueprint_step.unit_type
            label = blueprint_step.service + (f" ({blueprint_step.unit_tag})" if blueprint_step.unit_tag else "")
        else:
            unit_type, label = _unit_metadata(unit_id, separation_type)
        section = section_by_unit.get(unit_id)
        upstream_nodes = []
        downstream_nodes = []
        representative_stream_ids = []
        stream_roles: list[str] = []
        side_draw_stream_ids: list[str] = []
        for stream in stream_table.streams:
            if stream.destination_unit_id == unit_id and stream.source_unit_id and stream.source_unit_id != "battery_limits":
                if stream.source_unit_id not in upstream_nodes:
                    upstream_nodes.append(stream.source_unit_id)
                representative_stream_ids.append(stream.stream_id)
                if stream.stream_role and stream.stream_role not in stream_roles:
                    stream_roles.append(stream.stream_role)
            if stream.source_unit_id == unit_id and stream.destination_unit_id:
                if stream.destination_unit_id not in downstream_nodes:
                    downstream_nodes.append(stream.destination_unit_id)
                representative_stream_ids.append(stream.stream_id)
                if stream.stream_role and stream.stream_role not in stream_roles:
                    stream_roles.append(stream.stream_role)
                if stream.stream_role == "side_draw":
                    side_draw_stream_ids.append(stream.stream_id)
        node_notes: list[str] = []
        if section is not None:
            node_notes.append(f"Section `{section.section_id}` / `{section.section_type}`.")
            if section.side_draw_stream_ids:
                node_notes.append(f"Section side draws: {', '.join(section.side_draw_stream_ids)}.")
        if blueprint_step is not None:
            node_notes.append(
                f"Blueprint section `{blueprint_step.section_id}` / `{blueprint_step.section_label}` as `{blueprint_step.step_role}`."
            )
            if blueprint_step.notes:
                node_notes.append(" ".join(blueprint_step.notes))
        if recycle_loops_by_source.get(unit_id):
            node_notes.append(f"Recycle loops: {', '.join(recycle_loops_by_source[unit_id])}.")
        nodes.append(
            FlowsheetNode(
                node_id=unit_id,
                unit_type=unit_type,
                label=label,
                section_id=section.section_id if section is not None else "",
                section_type=section.section_type if section is not None else "",
                upstream_nodes=upstream_nodes,
                downstream_nodes=downstream_nodes,
                representative_stream_ids=sorted(dict.fromkeys(representative_stream_ids)),
                stream_roles=stream_roles,
                recycle_loop_ids=sorted(recycle_loops_by_source.get(unit_id, [])),
                side_draw_stream_ids=sorted(dict.fromkeys(side_draw_stream_ids)),
                notes=" ".join(node_notes),
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
                    substitutions={
                        "operating_mode": operating_mode,
                        "route_id": route.route_id,
                        "section_id": node.section_id or "unsectioned",
                        "stream_roles": ", ".join(node.stream_roles) or "intermediate",
                    },
                    result="configured",
                    notes="Generic flowsheet graph is now seeded from the selected route, stream table, and sectioned topology.",
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
            "| Node | Section | Unit Type | Upstream | Downstream | Representative Streams | Roles |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {node.node_id} | {node.section_id or '-'} | {node.unit_type} | {', '.join(node.upstream_nodes) or '-'} | {', '.join(node.downstream_nodes) or '-'} | {', '.join(node.representative_stream_ids) or '-'} | {', '.join(node.stream_roles) or '-'} |"
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
        section_ids=[section.section_id for section in stream_table.sections],
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
    utility_types = {item.utility_type.lower(): item for item in utility_summary.items}

    def _make_loop(
        *,
        control_id: str,
        unit_id: str,
        loop_family: str,
        controlled_variable: str,
        manipulated_variable: str,
        sensor: str,
        actuator: str,
        objective: str,
        disturbance_basis: str,
        startup_logic: str,
        shutdown_logic: str,
        override_logic: str,
        safeguard_linkage: str,
        criticality: str,
        notes: str,
    ) -> ControlLoop:
        return ControlLoop(
            control_id=control_id,
            unit_id=unit_id,
            loop_family=loop_family,
            controlled_variable=controlled_variable,
            manipulated_variable=manipulated_variable,
            sensor=sensor,
            actuator=actuator,
            objective=objective,
            disturbance_basis=disturbance_basis,
            startup_logic=startup_logic,
            shutdown_logic=shutdown_logic,
            override_logic=override_logic,
            safeguard_linkage=safeguard_linkage,
            criticality=criticality,
            notes=notes,
            citations=route.citations,
            assumptions=route.assumptions,
        )

    for item in equipment.items:
        lowered = item.equipment_type.lower()
        service_lower = item.service.lower()
        if "reactor" in lowered:
            loops.append(
                _make_loop(
                    control_id=f"TIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="temperature_cascade",
                    controlled_variable=f"{item.service} temperature",
                    manipulated_variable="Cooling or heating duty",
                    sensor="Temperature transmitter",
                    actuator="Control valve",
                    objective="Maintain reactor temperature within the conversion/selectivity window.",
                    disturbance_basis="Reaction heat release, feed-ratio drift, and utility temperature fluctuations.",
                    startup_logic="Ramp utility service first, then introduce feed under low-rate permissive until reactor temperature stabilizes.",
                    shutdown_logic="Isolate feeds, hold cooling/inerting until the reactor contents fall below the safe residual-temperature limit.",
                    override_logic="High-high temperature override closes feed and drives maximum cooling / quench response.",
                    safeguard_linkage="Feeds reactor runaway protection, utility permissives, and emergency feed isolation logic.",
                    criticality="high",
                    notes="Protects conversion and selectivity while limiting thermal upset.",
                )
            )
            loops.append(
                _make_loop(
                    control_id=f"PIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="pressure_override",
                    controlled_variable=f"{item.service} pressure",
                    manipulated_variable="Back-pressure control",
                    sensor="Pressure transmitter",
                    actuator="Control valve",
                    objective="Keep the reactor inside the design-pressure and phase-stability envelope.",
                    disturbance_basis="Gas evolution, condenser instability, and downstream restriction changes.",
                    startup_logic="Hold reactor on pressure trim while vent / recycle path is proven open before feed escalation.",
                    shutdown_logic="Depressure through the controlled path after feed isolation and maintain inert purge if required.",
                    override_logic="High-pressure override opens relief / vent control path and blocks further feed increase.",
                    safeguard_linkage="Supports relief sizing assumptions, pressure alarms, and shutdown permissives.",
                    criticality="high",
                    notes="Maintains design pressure envelope.",
                )
            )
            loops.append(
                _make_loop(
                    control_id=f"FRC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="feed_ratio",
                    controlled_variable=f"{item.service} feed ratio",
                    manipulated_variable="Lead/lag feed flow trim",
                    sensor="Ratio station with flow transmitters",
                    actuator="Feed control valve / VFD",
                    objective="Maintain stoichiometric or dilution ratio through startup and steady operation.",
                    disturbance_basis="Upstream feed composition change and pump-speed drift.",
                    startup_logic="Keep secondary feed on ratio-follow mode to the lead feed until circulation and temperature are stable.",
                    shutdown_logic="Drive secondary feed closed first, then ramp down the lead feed to avoid off-ratio inventory.",
                    override_logic="High-reactor-temperature or low-circulation permissive forces low-feed bias and ratio hold.",
                    safeguard_linkage="Links throughput control to reactor temperature and pressure safeguard logic.",
                    criticality="high" if any(h.severity == "high" for h in route.hazards) else "medium",
                    notes="Maintains feed ratio and protects reactor selectivity assumptions.",
                )
            )
        elif "process unit" in lowered or "column" in lowered:
            loops.append(
                _make_loop(
                    control_id=f"LIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="inventory_level",
                    controlled_variable=f"{item.service} level",
                    manipulated_variable="Bottoms withdrawal",
                    sensor="Level transmitter",
                    actuator="Control valve",
                    objective="Maintain bottoms inventory and protect internals from flooding or dry operation.",
                    disturbance_basis="Feed swings, vapor-rate changes, and downstream withdrawal interruptions.",
                    startup_logic="Establish reflux / circulation first, then release bottoms under minimum-level permissive.",
                    shutdown_logic="Reduce feed, maintain reflux / boil-up as needed, and drain to the safe low-level setpoint.",
                    override_logic="High-high level overrides bottoms withdrawal or feed cutback depending on service family.",
                    safeguard_linkage="Protects internals, reboiler circulation, and downstream product-quality stability.",
                    criticality="medium",
                    notes="Protects internals and downstream product quality.",
                )
            )
            loops.append(
                _make_loop(
                    control_id=f"PIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="pressure_regulatory",
                    controlled_variable=f"{item.service} pressure",
                    manipulated_variable="Condenser or vent-duty trim",
                    sensor="Pressure transmitter",
                    actuator="Control valve",
                    objective="Hold the main separation unit on its target pressure / vacuum basis.",
                    disturbance_basis="Condenser duty swings, vent-load changes, and upstream composition disturbance.",
                    startup_logic="Pull pressure into band before advancing feed and enabling automatic reflux or solvent circulation.",
                    shutdown_logic="Unload feed, keep pressure control active during rundown, then isolate to safe ambient / inert condition.",
                    override_logic="Low-pressure / high-pressure override biases vent or condenser duty to prevent air ingress or overpressure.",
                    safeguard_linkage="Feeds column pressure alarms, vacuum protection, and offgas routing logic.",
                    criticality="high" if ("column" in lowered or "distillation" in service_lower) else "medium",
                    notes="Maintains pressure envelope for distillation, absorption, or other main process-unit service.",
                )
            )
            loops.append(
                _make_loop(
                    control_id=f"FIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="quality_reflux_or_solvent",
                    controlled_variable=f"{item.service} quality driver",
                    manipulated_variable="Reflux / solvent / circulation flow",
                    sensor="Flow transmitter with composition or ratio bias",
                    actuator="Control valve / VFD",
                    objective="Hold the separation-driving flow that protects product quality and capture/yield targets.",
                    disturbance_basis="Feed flow/composition variation and utility availability changes.",
                    startup_logic="Run on minimum stable recycle/reflux, then close quality target once pressure and inventory loops settle.",
                    shutdown_logic="Return manipulated flow to rundown minimum before stopping duty or feed sources.",
                    override_logic="Analyzer or high-differential-pressure override trims reflux / solvent / circulation to a safe fallback value.",
                    safeguard_linkage="Ties separation quality control to utility duty, flooding risk, and off-spec prevention.",
                    criticality="medium",
                    notes="Covers reflux control, solvent-rate control, or circulation control depending on selected process-unit family.",
                )
            )
        elif "storage" in lowered or "tank" in lowered:
            loops.append(
                _make_loop(
                    control_id=f"LIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="inventory_level",
                    controlled_variable=f"{item.service} level",
                    manipulated_variable="Dispatch pump permissive",
                    sensor="Level transmitter",
                    actuator="Pump trip",
                    objective="Prevent overflow and dry-running while maintaining dispatch-ready inventory.",
                    disturbance_basis="Filling / dispatch mismatch and restart buffer drawdown.",
                    startup_logic="Keep dispatch permissive blocked until minimum operating inventory is restored.",
                    shutdown_logic="Stop transfer on low-low level and retain restart inventory if the plant is entering outage mode.",
                    override_logic="High-high level override stops filling and opens alternate routing if configured.",
                    safeguard_linkage="Supports storage overflow protection and working-inventory assumptions.",
                    criticality="medium",
                    notes="Prevents overflow and dry running.",
                )
            )
            loops.append(
                _make_loop(
                    control_id=f"PIC-{item.equipment_id}",
                    unit_id=item.equipment_id,
                    loop_family="blanketing_pressure",
                    controlled_variable=f"{item.service} blanketing pressure",
                    manipulated_variable="Nitrogen make-up / vent trim",
                    sensor="Pressure transmitter",
                    actuator="Blanketing valve",
                    objective="Maintain safe storage pressure and inert atmosphere for inventory handling.",
                    disturbance_basis="Ambient temperature swing, filling surge, and dispatch withdrawal.",
                    startup_logic="Establish blanketing pressure before opening transfer inlets or outlets.",
                    shutdown_logic="Maintain minimum blanketing setpoint through static storage and isolation.",
                    override_logic="High-pressure / low-pressure override trims venting or nitrogen make-up ahead of tank relief action.",
                    safeguard_linkage="Links storage pressure control to inerting and vent-protection assumptions.",
                    criticality="medium" if "nitrogen" in utility_types else "low",
                    notes="Maintains tank blanketing and breathing protection.",
                )
            )
    if not loops:
        loops.append(
            _make_loop(
                control_id="FIC-101",
                unit_id="generic_feed_section",
                loop_family="feed_flow",
                controlled_variable="Feed flow",
                manipulated_variable="Feed pump speed",
                sensor="Flow transmitter",
                actuator="VFD",
                objective="Stabilize plant feed under the generic flowsheet fallback.",
                disturbance_basis="Upstream supply variation and downstream hydraulic disturbances.",
                startup_logic="Enable after downstream permissives are healthy and inventory is available.",
                shutdown_logic="Ramp to minimum before equipment isolation.",
                override_logic="Low-flow / downstream-trip permissive returns feed to safe minimum.",
                safeguard_linkage="Generic feed stabilization linkage for fallback flowsheet operation.",
                criticality="medium",
                notes="Generic feed stabilization loop.",
            )
        )
    utility_count = len(utility_summary.items)
    markdown = (
        f"The deterministic control plan derives {len(loops)} loops from {len(equipment.items)} major equipment items and {utility_count} utility services. "
        "Loops are attached to thermal, pressure, level, feed-stability, startup/shutdown, and override risks rather than generated as generic instrumentation text."
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
    loops_by_unit: dict[str, list[ControlLoop]] = {}
    for loop in control_plan.control_loops:
        loops_by_unit.setdefault(loop.unit_id or "", []).append(loop)

    def _loop_ids(unit_id: str, fallback_count: int = 2) -> list[str]:
        linked = [loop.control_id for loop in loops_by_unit.get(unit_id, [])]
        return linked or control_ids[:fallback_count]

    def _append_node(
        *,
        node_id: str,
        node_family: str,
        design_intent: str,
        parameter: str,
        guide_word: str,
        deviation: str,
        causes: list[str],
        consequences: list[str],
        safeguards: list[str],
        linked_control_loops: list[str],
        consequence_severity: str,
        recommendation_priority: str,
        recommendation: str,
    ) -> None:
        nodes.append(
            HazopNode(
                node_id=node_id,
                node_family=node_family,
                design_intent=design_intent,
                parameter=parameter,
                guide_word=guide_word,
                deviation=deviation,
                causes=causes,
                consequences=consequences,
                safeguards=safeguards,
                linked_control_loops=linked_control_loops,
                consequence_severity=consequence_severity,
                recommendation_priority=recommendation_priority,
                recommendation_status="open",
                recommendation=recommendation,
                citations=route.citations,
                assumptions=route.assumptions + control_plan.assumptions,
            )
        )

    for item in equipment.items:
        lowered = item.equipment_type.lower()
        if "reactor" in lowered:
            linked = _loop_ids(item.equipment_id)
            _append_node(
                node_id=item.equipment_id,
                node_family="reactor",
                design_intent="Maintain controlled conversion at safe temperature and pressure.",
                parameter="Temperature",
                guide_word="More",
                deviation="Higher than intended reactor temperature",
                causes=["Cooling failure", "Excess reactant feed", "Utility temperature excursion"],
                consequences=["Runaway tendency", "Selectivity loss", "Pressure rise and emergency shutdown risk"],
                safeguards=linked or ["High-temperature alarm"],
                linked_control_loops=linked,
                consequence_severity="high",
                recommendation_priority="high",
                recommendation="Add high-high temperature trip, emergency feed isolation, and confirm cooling-failure response sequence.",
            )
        elif "column" in lowered or "distillation" in lowered or "process unit" in lowered:
            linked = _loop_ids(item.equipment_id)
            service_lower = item.service.lower()
            if "absorption" in service_lower:
                _append_node(
                    node_id=item.equipment_id,
                    node_family="absorber",
                    design_intent="Maintain capture / stripping performance with stable pressure, solvent, and inventory control.",
                    parameter="Solvent flow",
                    guide_word="Less",
                    deviation="Lower than intended absorber solvent or circulation flow",
                    causes=["Pump trip", "Valve failure", "Blocked circulation path"],
                    consequences=["Reduced capture efficiency", "Offgas release", "Packing wetting loss"],
                    safeguards=linked or ["Low-flow alarm"],
                    linked_control_loops=linked,
                    consequence_severity="high" if any(h.severity == "high" for h in route.hazards) else "medium",
                    recommendation_priority="high",
                    recommendation="Add low-solvent-flow interlock and confirm offgas routing / bypass logic for absorber upset conditions.",
                )
            elif any(token in service_lower for token in ["crystallizer", "filter", "dryer"]):
                _append_node(
                    node_id=item.equipment_id,
                    node_family="solids_separation",
                    design_intent="Maintain crystallization / filtration / drying duty without solids carryover or moisture failure.",
                    parameter="Moisture / solids inventory",
                    guide_word="More",
                    deviation="Higher than intended moisture or slurry hold-up",
                    causes=["Poor filtration", "Dryer under-duty", "Circulation upset"],
                    consequences=["Wet product", "Plugging / fouling", "Off-spec solids handling"],
                    safeguards=linked or ["Moisture alarm"],
                    linked_control_loops=linked,
                    consequence_severity="medium",
                    recommendation_priority="medium",
                    recommendation="Verify moisture-endpoint alarms, slurry circulation permissives, and isolation for solids upset handling.",
                )
            else:
                _append_node(
                    node_id=item.equipment_id,
                    node_family="column_or_main_separation",
                    design_intent="Maintain stable separation pressure, inventory, and quality-driving internal flows.",
                    parameter="Pressure",
                    guide_word="Less",
                    deviation="Lower than intended main-separation pressure",
                    causes=["Vacuum overshoot", "Condenser instability", "Vent control malfunction"],
                    consequences=["Air ingress", "Column instability", "Off-spec separation performance"],
                    safeguards=linked or ["Pressure alarm"],
                    linked_control_loops=linked,
                    consequence_severity="high",
                    recommendation_priority="high",
                    recommendation="Protect low-pressure operation, verify oxygen ingress response, and confirm safe reflux / circulation fallback.",
                )
        elif "storage" in lowered or "tank" in lowered:
            linked = _loop_ids(item.equipment_id, fallback_count=1)
            _append_node(
                node_id=item.equipment_id,
                node_family="storage",
                design_intent="Hold safe inventory, containment, and blanketing during receipt, storage, and dispatch.",
                parameter="Level",
                guide_word="More",
                deviation="Higher than intended storage level",
                causes=["Blocked outlet", "Dispatch mismatch", "Filling valve left open"],
                consequences=["Overflow", "Containment loss", "Transfer spill / emissions event"],
                safeguards=linked or ["High-level alarm"],
                linked_control_loops=linked,
                consequence_severity="medium",
                recommendation_priority="medium",
                recommendation="Provide level interlocks, overflow routing checks, and confirm dispatch / receipt isolation logic.",
            )
        elif "exchanger" in lowered or "reboiler" in lowered or "condenser" in lowered:
            linked = _loop_ids(item.equipment_id)
            _append_node(
                node_id=item.equipment_id,
                node_family="thermal_exchange",
                design_intent="Deliver required thermal duty without tube-side / shell-side upset or loss of containment.",
                parameter="Heat transfer",
                guide_word="Less",
                deviation="Lower than intended thermal duty",
                causes=["Fouling", "Utility interruption", "Flow maldistribution"],
                consequences=["Poor temperature control", "Downstream off-spec operation", "Potential pressure upset in linked unit"],
                safeguards=linked or ["Duty alarm"],
                linked_control_loops=linked,
                consequence_severity="medium",
                recommendation_priority="medium",
                recommendation="Confirm utility low-flow alarms, bypass logic, and exchanger isolation / cleaning response.",
            )
        elif "pump" in lowered or "compressor" in lowered or "blower" in lowered:
            linked = _loop_ids(item.equipment_id, fallback_count=1)
            _append_node(
                node_id=item.equipment_id,
                node_family="rotating_transfer",
                design_intent="Maintain reliable transfer / circulation flow without loss of suction or overpressure.",
                parameter="Flow",
                guide_word="Less",
                deviation="Lower than intended transfer flow",
                causes=["Pump trip", "Loss of suction", "Discharge blockage"],
                consequences=["Starved downstream section", "Dry running / damage", "Inventory imbalance"],
                safeguards=linked or ["Low-flow alarm"],
                linked_control_loops=linked,
                consequence_severity="medium",
                recommendation_priority="medium",
                recommendation="Verify low-flow trip, suction permissives, and downstream isolation / bypass response.",
            )
    if not nodes:
        for node in flowsheet_graph.nodes:
            _append_node(
                node_id=node.node_id,
                node_family="generic_flowsheet_node",
                design_intent="Maintain intended flow through the solved flowsheet section.",
                parameter="Flow",
                guide_word="No",
                deviation="No flow through the generic flowsheet node",
                causes=["Pump trip", "Valve isolation", "Control permissive failure"],
                consequences=["Starved downstream section", "Off-spec operation", "Potential recycle instability"],
                safeguards=["Flow alarm"],
                linked_control_loops=control_ids[:1],
                consequence_severity="medium",
                recommendation_priority="medium",
                recommendation="Confirm flow permissives and bypass / isolation response across the generic flowsheet.",
            )
    family_count = len({node.node_family for node in nodes})
    coverage_summary = f"{len(nodes)} HAZOP nodes across {family_count} node families derived from the selected flowsheet and equipment list."
    markdown = "### HAZOP Node Register\n\n" + "\n".join(
        [
            "| Node | Family | Parameter | Guide Word | Deviation | Causes | Consequences | Safeguards | Linked Loops | Recommendation |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {node.node_id} | {node.node_family} | {node.parameter} | {node.guide_word} | {node.deviation} | {'; '.join(node.causes)} | {'; '.join(node.consequences)} | {'; '.join(node.safeguards)} | {'; '.join(node.linked_control_loops) or '-'} | {node.recommendation} |"
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
