from __future__ import annotations

import html
import re

from aoc.models import (
    BlockFlowDiagramArtifact,
    ControlArchitectureDecision,
    ControlPlanArtifact,
    ControlSystemDiagramArtifact,
    DiagramAcceptanceArtifact,
    DiagramEdge,
    DiagramLabel,
    DiagramLayoutHints,
    DiagramNode,
    DiagramSheet,
    DiagramStyleProfile,
    DiagramTargetProfile,
    EnergyBalance,
    EquipmentListArtifact,
    FlowsheetBlueprintArtifact,
    FlowsheetCase,
    FlowsheetGraph,
    ProcessFlowDiagramArtifact,
    ProjectBasis,
    StreamTable,
)


def build_diagram_style_profile() -> DiagramStyleProfile:
    return DiagramStyleProfile(
        style_id="academic_process_diagrams_v1",
        style_name="Academic Chemical Engineering Diagrams",
        markdown=(
            "### Diagram Style Profile\n\n"
            "- Clean academic SVG rendering\n"
            "- Deterministic layout\n"
            "- Distinct handling for main process, recycle, utility, vent, and waste paths\n"
        ),
    )


def build_diagram_target_profile(project_basis: ProjectBasis) -> DiagramTargetProfile:
    product_key = re.sub(r"[^a-z0-9]+", "_", project_basis.target_product.lower()).strip("_") or "project"
    return DiagramTargetProfile(
        target_id=f"{product_key}_diagram_target_v1",
        target_product=project_basis.target_product,
        required_bfd_sections=[
            "feed preparation",
            "reaction",
            "cleanup",
            "concentration",
            "purification",
            "storage",
            "waste handling",
        ],
        required_pfd_unit_families=[
            "reactor",
            "separator",
            "column",
            "vessel",
            "heat exchanger",
            "tank",
            "pump",
        ],
        major_stream_roles=["feed", "product", "recycle", "purge", "vent", "waste", "side_draw"],
        main_body_max_pfd_nodes=6,
        markdown=(
            "### Diagram Target Profile\n\n"
            "- BAC-first BFD/PFD drawing rules\n"
            "- BFD stays section-level\n"
            "- PFD stays report-grade equipment-level rather than full P&ID detail\n"
        ),
    )


def build_block_flow_diagram(
    blueprint: FlowsheetBlueprintArtifact,
    style: DiagramStyleProfile,
    target: DiagramTargetProfile,
) -> BlockFlowDiagramArtifact:
    section_nodes: list[DiagramNode] = []
    section_index: dict[str, str] = {}
    section_order: list[str] = []
    section_transition_pairs: list[tuple[str, str]] = []
    step_to_section: dict[str, str] = {}

    def register_section(section_key: str, display_label: str) -> str:
        if section_key in section_index:
            return section_index[section_key]
        node_id = f"bfd_{re.sub(r'[^a-z0-9]+', '_', section_key.lower()).strip('_') or 'section'}"
        section_index[section_key] = node_id
        section_order.append(section_key)
        section_nodes.append(
            DiagramNode(
                node_id=node_id,
                label=display_label,
                node_family="process_block",
                section_id=section_key,
                labels=[DiagramLabel(text=display_label)],
            )
        )
        return node_id

    previous_section_key = ""
    for step in blueprint.steps:
        section_key = _canonical_bfd_section(step.section_label or step.section_id or step.service)
        step_to_section[step.step_id] = section_key
        display_label = _display_bfd_section(section_key)
        register_section(section_key, display_label)
        if previous_section_key and previous_section_key != section_key:
            pair = (previous_section_key, section_key)
            if pair not in section_transition_pairs:
                section_transition_pairs.append(pair)
        previous_section_key = section_key

    for required in target.required_bfd_sections:
        if required in section_index:
            continue
        if any(required in present for present in section_index):
            continue
        register_section(required, _display_bfd_section(required))

    _layout_linear_nodes(section_nodes, style, y=250, width=220, height=88, x_start=90, x_gap=52)

    edges: list[DiagramEdge] = []
    edge_counter = 1
    for left_key, right_key in section_transition_pairs:
        edges.append(
            DiagramEdge(
                edge_id=f"bfd_edge_{edge_counter}",
                source_node_id=section_index[left_key],
                target_node_id=section_index[right_key],
                edge_type="main",
                label="Main process flow",
            )
        )
        edge_counter += 1

    for recycle in blueprint.recycle_intents:
        source_key = step_to_section.get(recycle.source_step_id, _canonical_bfd_section(recycle.source_step_id))
        target_key = step_to_section.get(recycle.target_step_id, _canonical_bfd_section(recycle.target_step_id))
        if source_key not in section_index or target_key not in section_index:
            continue
        label = target.recycle_notation
        if recycle.stream_family:
            label = f"{label} ({recycle.stream_family.replace('_', ' ')})"
        edges.append(
            DiagramEdge(
                edge_id=f"bfd_edge_{edge_counter}",
                source_node_id=section_index[source_key],
                target_node_id=section_index[target_key],
                edge_type="recycle",
                label=label,
            )
        )
        edge_counter += 1

    dynamic_width = max(style.canvas_width_px, int(max((node.x + node.width) for node in section_nodes) + 80))
    sheet = DiagramSheet(
        sheet_id="sheet_1",
        title="Block Flow Diagram",
        width_px=dynamic_width,
        height_px=max(style.canvas_height_px, 820),
        orientation="landscape",
        presentation_mode="sheet",
        preferred_scale=1.0,
        full_page=True,
        legend_mode="suppressed",
        suppress_inline_wrapping=True,
        node_ids=[node.node_id for node in section_nodes],
        edge_ids=[edge.edge_id for edge in edges],
    )
    sheet.svg = _render_svg(sheet, section_nodes, edges, style, subtitle="Section-level process representation")
    mermaid_fallback = _mermaid_from_diagram(section_nodes, edges, orientation="LR")
    markdown = (
        "### Diagram Basis\n\n"
        "The block flow diagram below shows only the major process sections and the key recycle logic required to explain the selected route.\n"
    )
    return BlockFlowDiagramArtifact(
        diagram_id=f"{blueprint.route_id}_bfd",
        route_id=blueprint.route_id,
        nodes=section_nodes,
        edges=edges,
        sheets=[sheet],
        mermaid_fallback=mermaid_fallback,
        citations=blueprint.citations,
        assumptions=blueprint.assumptions
        + [
            "BFD is intentionally simplified to section-level blocks for academic report readability.",
            "Only major recycle and side-flow logic is shown on the BFD.",
        ],
        markdown=markdown,
    )


def build_process_flow_diagram(
    flowsheet_graph: FlowsheetGraph,
    flowsheet_case: FlowsheetCase,
    stream_table: StreamTable,
    equipment: EquipmentListArtifact | None,
    energy_balance: EnergyBalance | None,
    style: DiagramStyleProfile,
    target: DiagramTargetProfile,
    control_plan: ControlPlanArtifact | None = None,
) -> ProcessFlowDiagramArtifact:
    equipment_index = {item.equipment_id: item for item in (equipment.items if equipment is not None else [])}
    equipment_items = equipment.items if equipment is not None else []
    stream_index = {stream.stream_id: stream for stream in stream_table.streams}
    utility_note_by_unit: dict[str, str] = {}
    if energy_balance is not None:
        for duty in energy_balance.duties:
            note_parts: list[str] = []
            if duty.heating_kw > 0:
                note_parts.append(f"+{duty.heating_kw:.0f} kW heat")
            if duty.cooling_kw > 0:
                note_parts.append(f"+{duty.cooling_kw:.0f} kW cool")
            if note_parts:
                utility_note_by_unit[duty.unit_id] = ", ".join(note_parts)

    nodes: list[DiagramNode] = []
    loops_by_unit: dict[str, list[str]] = {}
    if control_plan is not None:
        for loop in control_plan.control_loops:
            if loop.unit_id:
                loops_by_unit.setdefault(loop.unit_id, []).append(loop.control_id)
    for rank, node in enumerate(flowsheet_graph.nodes):
        equipment_tag, display_label, node_family, equipment_item = _resolve_pfd_identity(
            node,
            equipment_items,
            target,
        )
        labels = [DiagramLabel(text=equipment_tag, kind="primary")]
        labels.append(DiagramLabel(text=display_label, kind="secondary"))
        loop_ids = _control_loop_ids_for_node(node, equipment_item.equipment_id if equipment_item is not None else "", loops_by_unit)
        if loop_ids:
            labels.append(DiagramLabel(text=", ".join(loop_ids[:2]), kind="utility"))
        if utility_note_by_unit.get(node.node_id):
            labels.append(DiagramLabel(text=utility_note_by_unit[node.node_id], kind="utility"))
        nodes.append(
            DiagramNode(
                node_id=node.node_id,
                label=node.label,
                node_family=node_family,
                section_id=node.section_id,
                equipment_tag=equipment_tag,
                labels=labels,
                layout=DiagramLayoutHints(rank=rank),
                notes=node.notes,
            )
        )

    terminal_node_ids: set[str] = {node.node_id for node in nodes}
    source_override_by_stream: dict[str, str] = {}
    destination_override_by_stream: dict[str, str] = {}
    terminal_counter = len(nodes) + 1
    for stream in flowsheet_case.streams:
        if stream.stream_role not in target.major_stream_roles:
            continue
        if stream.destination_unit_id is None and stream.source_unit_id:
            terminal_id = f"terminal_{stream.stream_role}_{terminal_counter}"
            if terminal_id not in terminal_node_ids:
                nodes.append(
                    DiagramNode(
                        node_id=terminal_id,
                        label=f"{stream.stream_role.title()} Outlet",
                        node_family="terminal",
                        section_id=stream.section_id,
                        equipment_tag=terminal_id,
                        labels=[
                            DiagramLabel(text=f"{stream.stream_role.title()} Outlet"),
                            DiagramLabel(text=stream.stream_id, kind="secondary"),
                        ],
                        layout=DiagramLayoutHints(rank=terminal_counter),
                    )
                )
                terminal_node_ids.add(terminal_id)
                terminal_counter += 1
            destination_override_by_stream[stream.stream_id] = terminal_id
        elif stream.source_unit_id is None and stream.destination_unit_id:
            terminal_id = f"terminal_feed_{terminal_counter}"
            if terminal_id not in terminal_node_ids:
                nodes.append(
                    DiagramNode(
                        node_id=terminal_id,
                        label="Feed Inlet",
                        node_family="terminal",
                        section_id=stream.section_id,
                        equipment_tag=terminal_id,
                        labels=[DiagramLabel(text="Feed Inlet"), DiagramLabel(text=stream.stream_id, kind="secondary")],
                        layout=DiagramLayoutHints(rank=terminal_counter),
                    )
                )
                terminal_node_ids.add(terminal_id)
                terminal_counter += 1
            source_override_by_stream[stream.stream_id] = terminal_id

    sheets = _build_pfd_sheets(nodes, style, target)
    node_lookup = {node.node_id: node for node in nodes}
    for sheet in sheets:
        sheet_node_lookup = {node_id: node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup}
        _layout_sheet_nodes(list(sheet_node_lookup.values()), style, sheet.title)
        if _is_bac_target(target):
            _apply_bac_pfd_layout(sheet, list(sheet_node_lookup.values()))
        if sheet_node_lookup:
            max_x = max(node.x + node.width for node in sheet_node_lookup.values())
            max_y = max(node.y + node.height for node in sheet_node_lookup.values())
            sheet.width_px = max(sheet.width_px, int(max_x + 220))
            sheet.height_px = max(sheet.height_px, int(max_y + 180))

    edges: list[DiagramEdge] = []
    edge_counter = 1
    node_sheet_lookup = {node_id: sheet.sheet_id for sheet in sheets for node_id in sheet.node_ids}
    for stream in flowsheet_case.streams:
        source_unit_id = source_override_by_stream.get(stream.stream_id, stream.source_unit_id or "")
        destination_unit_id = destination_override_by_stream.get(stream.stream_id, stream.destination_unit_id or "")
        if not source_unit_id or not destination_unit_id:
            continue
        if source_unit_id not in node_sheet_lookup or destination_unit_id not in node_sheet_lookup:
            continue
        if node_sheet_lookup[source_unit_id] != node_sheet_lookup[destination_unit_id]:
            continue
        source_stream = stream_index.get(stream.stream_id)
        stream_description = source_stream.description if source_stream is not None else ""
        if _is_bac_target(target):
            label, show_condition = _bac_stream_callout(stream.stream_id, stream_description, stream.stream_role)
        else:
            label = _pfd_stream_label(stream.stream_id, stream_description, stream.stream_role)
            show_condition = bool(source_stream is not None and stream.stream_role == "main")
        condition_label = ""
        if show_condition and source_stream is not None and source_stream.temperature_c and source_stream.pressure_bar:
            condition_label = f"{source_stream.temperature_c:.0f} C / {source_stream.pressure_bar:.1f} bar"
        edges.append(
            DiagramEdge(
                edge_id=f"pfd_edge_{edge_counter}",
                source_node_id=source_unit_id,
                target_node_id=destination_unit_id,
                edge_type=_edge_type_from_role(stream.stream_role),
                stream_id=stream.stream_id,
                label=label,
                condition_label=condition_label,
                sheet_id=node_sheet_lookup[source_unit_id],
            )
        )
        edge_counter += 1

    for loop in flowsheet_case.recycle_loops:
        if not loop.recycle_source_unit_id or not loop.recycle_target_unit_id:
            continue
        if loop.recycle_source_unit_id not in node_sheet_lookup or loop.recycle_target_unit_id not in node_sheet_lookup:
            continue
        if node_sheet_lookup[loop.recycle_source_unit_id] != node_sheet_lookup[loop.recycle_target_unit_id]:
            continue
        if loop.recycle_stream_ids and any(
            edge.stream_id in set(loop.recycle_stream_ids)
            and edge.source_node_id == loop.recycle_source_unit_id
            and edge.target_node_id == loop.recycle_target_unit_id
            for edge in edges
        ):
            continue
        label = "Recycle loop"
        edges.append(
            DiagramEdge(
                edge_id=f"pfd_edge_{edge_counter}",
                source_node_id=loop.recycle_source_unit_id,
                target_node_id=loop.recycle_target_unit_id,
                edge_type="recycle",
                label=label,
                sheet_id=node_sheet_lookup[loop.recycle_source_unit_id],
            )
        )
        edge_counter += 1

    sheet_lookup = {sheet.sheet_id: sheet for sheet in sheets}
    for edge in edges:
        sheet_lookup[edge.sheet_id].edge_ids.append(edge.edge_id)
    for sheet in sheets:
        sheet_nodes = [node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup]
        sheet_edges = [edge for edge in edges if edge.sheet_id == sheet.sheet_id]
        sheet.svg = _render_svg(sheet, sheet_nodes, sheet_edges, style, subtitle="Equipment-level process flow representation")

    markdown = (
        "### Diagram Basis\n\n"
        "The process flow diagram below shows the major equipment items, stream directions, recycle paths, and principal vent/product/waste branches required to support the design chapters.\n"
    )
    return ProcessFlowDiagramArtifact(
        diagram_id=f"{flowsheet_graph.route_id}_pfd",
        route_id=flowsheet_graph.route_id,
        nodes=nodes,
        edges=edges,
        sheets=sheets,
        citations=sorted(set(flowsheet_graph.citations + flowsheet_case.citations + stream_table.citations)),
        assumptions=flowsheet_graph.assumptions
        + flowsheet_case.assumptions
        + stream_table.assumptions
        + [
            "PFD is rendered as a report-grade equipment flow diagram rather than a full piping and instrumentation diagram.",
            "Large equipment-level trains may be split into multiple sheets for readability.",
        ],
        markdown=markdown,
    )


def build_control_system_diagram(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    flowsheet_graph: FlowsheetGraph,
    style: DiagramStyleProfile,
    flowsheet_case: FlowsheetCase | None = None,
) -> ControlSystemDiagramArtifact:
    loop_groups: dict[str, list] = {}
    unit_label_by_id = {node.node_id: node.label for node in flowsheet_graph.nodes}
    for loop in control_plan.control_loops:
        unit_id = loop.unit_id or "plant_supervisory"
        loop_groups.setdefault(unit_id, []).append(loop)

    ordered_unit_ids = [unit_id for unit_id in control_architecture.critical_units if unit_id in loop_groups]
    ordered_unit_ids.extend(unit_id for unit_id in loop_groups if unit_id not in ordered_unit_ids)
    ordered_unit_ids = ordered_unit_ids[:6]
    width_px = max(1700, 250 * max(4, len(ordered_unit_ids)) + 220)
    height_px = 980
    title = "Process Control Architecture"
    subtitle = control_architecture.decision.selected_candidate_id or "Supervisory architecture"
    dcs_label = _display_equipment_label(subtitle.replace("_", " "))
    svg = _render_control_system_svg(
        width_px,
        height_px,
        title=title,
        subtitle=dcs_label,
        unit_ids=ordered_unit_ids,
        loop_groups=loop_groups,
        unit_label_by_id=unit_label_by_id,
        style=style,
    )
    sheet = DiagramSheet(
        sheet_id="sheet_1",
        title=title,
        width_px=width_px,
        height_px=height_px,
        orientation="landscape",
        presentation_mode="sheet",
        preferred_scale=1.0,
        full_page=True,
        legend_mode="embedded",
        suppress_inline_wrapping=True,
        svg=svg,
    )
    sheets = [sheet]
    overlay_sheet = _build_instrumented_overlay_sheet(control_plan, control_architecture, style)
    sheets.append(overlay_sheet)
    markdown = (
        "### Diagram Basis\n\n"
        "The control-system diagrams below show the major controlled units, the principal loop clusters, and their supervisory control architecture for the selected BAC process.\n"
    )
    return ControlSystemDiagramArtifact(
        diagram_id=f"{flowsheet_graph.route_id}_control",
        route_id=flowsheet_graph.route_id,
        sheets=sheets,
        citations=sorted(set(control_plan.citations + control_architecture.citations + flowsheet_graph.citations)),
        assumptions=control_plan.assumptions
        + control_architecture.assumptions
        + flowsheet_graph.assumptions
        + [
            "Control diagram is rendered as a report-grade control architecture view rather than a full ISA instrument bubble sheet.",
            "Only the principal BAC loop clusters are shown to keep the figure readable in the main report body.",
            "The instrumented overlay links the principal loop IDs back to the major process units without expanding to full P&ID line-by-line detail.",
        ],
        markdown=markdown,
    )


def build_diagram_acceptance(
    *,
    diagram_kind: str,
    diagram_id: str,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    target: DiagramTargetProfile,
    blueprint: FlowsheetBlueprintArtifact | None = None,
    flowsheet_graph: FlowsheetGraph | None = None,
    flowsheet_case: FlowsheetCase | None = None,
) -> DiagramAcceptanceArtifact:
    missing_nodes: list[str] = []
    missing_edges: list[str] = []
    mismatched_labels: list[str] = []
    notes: list[str] = []
    node_labels = [node.label.lower() for node in nodes]
    edge_types = {edge.edge_type for edge in edges}

    if diagram_kind == "bfd":
        for required in target.required_bfd_sections:
            if not any(required in label or required in node.section_id.lower() for node, label in zip(nodes, node_labels)):
                missing_nodes.append(required)
        if blueprint is not None and blueprint.recycle_intents and "recycle" not in edge_types:
            missing_edges.append("recycle path")
        if not missing_nodes and not missing_edges:
            notes.append("BFD contains the major process sections and recycle logic expected for the selected BAC blueprint.")
    else:
        if flowsheet_graph is not None:
            graph_unit_ids = {node.node_id for node in flowsheet_graph.nodes}
            rendered_unit_ids = {node.node_id for node in nodes}
            for unit_id in sorted(graph_unit_ids - rendered_unit_ids):
                missing_nodes.append(unit_id)
        if flowsheet_case is not None:
            if any(loop.recycle_stream_ids for loop in flowsheet_case.recycle_loops) and "recycle" not in edge_types:
                missing_edges.append("recycle stream")
            outlet_edge_types = {edge.edge_type for edge in edges}
            for required_edge in ("product", "waste", "vent"):
                if required_edge == "vent":
                    vent_routed_with_waste = any(
                        stream.stream_role == "vent" and stream.destination_unit_id == "waste_treatment"
                        for stream in flowsheet_case.streams
                    ) and "waste" in outlet_edge_types
                    if vent_routed_with_waste:
                        continue
                if any(stream.stream_role == required_edge for stream in flowsheet_case.streams) and required_edge not in outlet_edge_types:
                    missing_edges.append(required_edge)
        if any("`" in node.label for node in nodes):
            mismatched_labels.append("Diagram labels still contain code-style quoting.")
        if not missing_nodes and not missing_edges and not mismatched_labels:
            notes.append("PFD contains the major units and stream roles expected from the solved flowsheet.")

    overall_status = "complete"
    if missing_nodes or missing_edges or mismatched_labels:
        overall_status = "conditional"
    markdown = (
        f"### {diagram_kind.upper()} Acceptance\n\n"
        f"- Missing required nodes: {', '.join(missing_nodes) or 'none'}\n"
        f"- Missing required edges: {', '.join(missing_edges) or 'none'}\n"
        f"- Label mismatches: {', '.join(mismatched_labels) or 'none'}\n"
    )
    return DiagramAcceptanceArtifact(
        diagram_id=diagram_id,
        diagram_kind="bfd" if diagram_kind == "bfd" else "pfd",
        overall_status=overall_status,
        missing_required_nodes=missing_nodes,
        missing_required_edges=missing_edges,
        mismatched_labels=mismatched_labels,
        notes=notes,
        markdown=markdown,
        citations=(blueprint.citations if blueprint is not None else [])
        or (flowsheet_graph.citations if flowsheet_graph is not None else [])
        or [],
        assumptions=(blueprint.assumptions if blueprint is not None else [])
        or (flowsheet_graph.assumptions if flowsheet_graph is not None else [])
        or [],
    )


def diagram_svg_fence(svg: str) -> str:
    return f"```diagram-svg\n{svg}\n```"


def _canonical_bfd_section(text: str) -> str:
    lowered = text.replace("_", " ").lower()
    if any(token in lowered for token in ("feed", "charge", "preparation", "make-up")):
        return "feed preparation"
    if any(token in lowered for token in ("reaction", "quaternization", "reactor")):
        return "reaction"
    if any(token in lowered for token in ("flash", "volatile", "cleanup", "neutralization", "primary recovery")):
        return "cleanup"
    if "concentration" in lowered or "evap" in lowered:
        return "concentration"
    if any(token in lowered for token in ("purification", "distillation", "separation", "polishing")):
        return "purification"
    if any(token in lowered for token in ("storage", "dispatch", "pack")):
        return "storage"
    if any(token in lowered for token in ("waste", "effluent", "scrub", "vent")):
        return "waste handling"
    return lowered.strip() or "process section"


def _display_bfd_section(section_key: str) -> str:
    return section_key.title().replace("Bfd", "BFD").replace("Pfd", "PFD")


def _layout_linear_nodes(
    nodes: list[DiagramNode],
    style: DiagramStyleProfile,
    *,
    y: float,
    width: float,
    height: float,
    x_start: float,
    x_gap: float,
) -> None:
    x = x_start
    for node in nodes:
        node.width = width
        node.height = height
        node.x = x
        node.y = y
        x += width + x_gap


def _pfd_node_family(unit_type: str, label: str) -> str:
    lowered = f"{unit_type} {label}".lower()
    if any(token in lowered for token in ("compressor", "blower")):
        return "compressor"
    if any(token in lowered for token in ("condenser", "reboiler")):
        return "condenser"
    if any(token in lowered for token in ("reactor", "cstr", "pfr")):
        return "reactor"
    if any(token in lowered for token in ("column", "distillation")):
        return "column"
    if any(token in lowered for token in ("pump",)):
        return "pump"
    if any(token in lowered for token in ("tank", "storage")):
        return "tank"
    if any(token in lowered for token in ("flash", "drum", "vessel", "separator")):
        return "vessel"
    if any(token in lowered for token in ("exchanger", "heater", "cooler", "condenser", "reboiler")):
        return "heat exchanger"
    if "terminal" in lowered:
        return "terminal"
    return "separator"


def _resolve_pfd_identity(node, equipment_items, target: DiagramTargetProfile):
    base_family = _pfd_node_family(node.unit_type, node.label)
    if _is_bac_target(target):
        mapping = {
            "reactor": ("R-101", "Jacketed CSTR Reactor", "bac_reactor"),
            "primary_flash": ("V-101", "Primary Flash Drum", "bac_flash_drum"),
            "purification": ("PU-201", "Purification Column", "bac_purification_column"),
            "storage": ("TK-301", "Product Storage Tank", "bac_storage_tank"),
            "concentration": ("E-101", "Concentration / Cleanup Exchanger", "bac_exchanger_package"),
            "feed_prep": ("M-101", "Feed Preparation Vessel", "bac_premix_vessel"),
            "waste_treatment": ("WT-401", "Waste / Purge Receiver", "bac_waste_receiver"),
        }
        if node.node_id in mapping:
            tag, label, family = mapping[node.node_id]
            equipment_item = next((item for item in equipment_items if item.equipment_id == tag), None)
            return tag, label, family, equipment_item
    equipment_item = None
    for item in equipment_items:
        if item.equipment_id == node.node_id:
            equipment_item = item
            break
    equipment_tag = equipment_item.equipment_id if equipment_item is not None else node.node_id.upper()
    display_label = _display_equipment_label(node.label)
    return equipment_tag, display_label, base_family, equipment_item


def _build_pfd_sheets(nodes: list[DiagramNode], style: DiagramStyleProfile, target: DiagramTargetProfile) -> list[DiagramSheet]:
    default_width = max(style.canvas_width_px, 2050 if _is_bac_target(target) else style.canvas_width_px)
    default_height = max(style.canvas_height_px, 1080 if _is_bac_target(target) else style.canvas_height_px)
    if not _should_split_pfd_sheet(nodes, target):
        return [
            DiagramSheet(
                sheet_id="sheet_1",
                title="Process Flow Diagram",
                width_px=max(default_width, int(len(nodes) * 260 + 260)),
                height_px=max(default_height, 940),
                orientation="landscape",
                presentation_mode="sheet",
                preferred_scale=1.0,
                full_page=True,
                legend_mode="embedded",
                suppress_inline_wrapping=True,
                node_ids=[node.node_id for node in nodes],
            )
        ]

    grouped: list[tuple[str, list[str]]] = []
    buckets: dict[str, list[str]] = {}
    for node in nodes:
        bucket = _sheet_title_for_section(node.section_id)
        buckets.setdefault(bucket, []).append(node.node_id)
    for title, node_ids in buckets.items():
        grouped.append((title, node_ids))
    sheets: list[DiagramSheet] = []
    for index, (title, node_ids) in enumerate(grouped, start=1):
        sheets.append(
            DiagramSheet(
                sheet_id=f"sheet_{index}",
                title=title,
                width_px=max(default_width, int(len(node_ids) * 250 + 240)),
                height_px=max(default_height, 940),
                orientation="landscape",
                presentation_mode="sheet",
                preferred_scale=1.0,
                full_page=True,
                legend_mode="embedded",
                suppress_inline_wrapping=True,
                node_ids=node_ids,
            )
        )
    return sheets


def _should_split_pfd_sheet(nodes: list[DiagramNode], target: DiagramTargetProfile) -> bool:
    if _is_bac_target(target):
        return True
    if len(nodes) > target.main_body_max_pfd_nodes:
        return True
    if len(nodes) < max(4, target.main_body_max_pfd_nodes):
        return False
    density_score = 0
    for node in nodes:
        label_count = len(node.labels)
        if label_count >= 3:
            density_score += 2
        elif label_count == 2:
            density_score += 1
        longest_label = max((len(label.text) for label in node.labels), default=0)
        if longest_label >= 24:
            density_score += 1
        if node.node_family in {"reactor", "column", "tank", "heat exchanger"}:
            density_score += 1
    return density_score >= max(8, len(nodes) + 2)


def _sheet_title_for_section(section_id: str) -> str:
    lowered = section_id.replace("_", " ").lower()
    if any(token in lowered for token in ("feed", "reaction", "prep", "cleanup", "concentration", "flash", "recovery")):
        return "PFD Sheet 1: Feed, Reaction, and Cleanup"
    if any(token in lowered for token in ("purification", "separation", "storage", "waste", "utility", "dispatch", "offsite")):
        return "PFD Sheet 2: Purification, Storage, and Offsites"
    return "PFD Sheet 2: Purification, Storage, and Offsites"


def _layout_sheet_nodes(nodes: list[DiagramNode], style: DiagramStyleProfile, title: str) -> None:
    family_lane = {
        "reactor": 0,
        "bac_reactor": 0,
        "compressor": 0,
        "heat exchanger": 1,
        "condenser": 1,
        "separator": 1,
        "column": 1,
        "bac_purification_column": 1,
        "vessel": 1,
        "bac_premix_vessel": 1,
        "bac_flash_drum": 1,
        "bac_exchanger_package": 1,
        "bac_waste_receiver": 1,
        "pump": 2,
        "tank": 2,
        "bac_storage_tank": 2,
        "terminal": 1,
    }
    section_bucket = {
        "feed": 0,
        "reaction": 1,
        "cleanup": 2,
        "concentration": 3,
        "purification": 4,
        "storage": 5,
        "waste": 6,
    }
    def _section_rank(section_id: str) -> int:
        lowered = section_id.replace("_", " ").lower()
        for token, rank in section_bucket.items():
            if token in lowered:
                return rank
        return 99

    nodes.sort(key=lambda node: (_section_rank(node.section_id), node.layout.rank, node.equipment_tag))
    x = 90.0
    for index, node in enumerate(nodes):
        lane = family_lane.get(node.node_family, 1)
        node.layout.lane = f"lane_{lane}"
        if node.node_family in {"column", "bac_purification_column"}:
            node.width = 150
            node.height = 190
        elif node.node_family == "pump":
            node.width = 170
            node.height = 92
        elif node.node_family == "compressor":
            node.width = 190
            node.height = 96
        elif node.node_family == "bac_reactor":
            node.width = 220
            node.height = 176
        elif node.node_family == "bac_premix_vessel":
            node.width = 214
            node.height = 142
        elif node.node_family == "bac_flash_drum":
            node.width = 220
            node.height = 132
        elif node.node_family == "bac_storage_tank":
            node.width = 194
            node.height = 158
        elif node.node_family == "bac_waste_receiver":
            node.width = 206
            node.height = 136
        elif node.node_family in {"reactor", "tank", "vessel", "separator"}:
            node.width = 190
            node.height = 150
        elif node.node_family == "bac_exchanger_package":
            node.width = 230
            node.height = 116
        elif node.node_family in {"heat exchanger", "condenser"}:
            node.width = 205
            node.height = 104
        else:
            node.width = 190
            node.height = 104
        node.x = x
        node.y = 150 + lane * 235
        x += node.width + 92


def _is_bac_target(target: DiagramTargetProfile) -> bool:
    lowered = target.target_product.lower()
    return "benzalkonium" in lowered or "bac" == lowered.strip()


def _bac_pfd_layout_map() -> dict[str, dict[str, object]]:
    return {
        "PFD Sheet 1: Feed, Reaction, and Cleanup": {
            "node_positions": {
                "feed_prep": (330.0, 322.0),
                "reactor": (708.0, 252.0),
                "primary_flash": (1048.0, 260.0),
                "concentration": (1460.0, 280.0),
                "waste_treatment": (1758.0, 282.0),
            },
            "terminal_positions": {
                "S-101": (118.0, 238.0),
                "S-102": (118.0, 408.0),
            },
            "fallback_origin": (160.0, 676.0),
            "fallback_step_y": 44.0,
        },
        "PFD Sheet 2: Purification, Storage, and Offsites": {
            "node_positions": {
                "purification": (278.0, 246.0),
                "storage": (820.0, 176.0),
                "waste_treatment": (826.0, 482.0),
            },
            "terminal_positions": {
                "S-401": (112.0, 122.0),
                "S-402": (1278.0, 190.0),
                "S-404": (1278.0, 358.0),
                "S-403": (1278.0, 546.0),
            },
            "fallback_origin": (1568.0, 708.0),
            "fallback_step_y": 44.0,
        },
    }


def _apply_bac_pfd_layout(sheet: DiagramSheet, nodes: list[DiagramNode]) -> None:
    layout_map = _bac_pfd_layout_map().get(sheet.title)
    if layout_map is None:
        return

    title = sheet.title.lower()

    def _node_has_stream(node: DiagramNode, stream_id: str) -> bool:
        return any(label.text.strip().upper() == stream_id.upper() for label in node.labels)

    def _match_position(node: DiagramNode) -> tuple[float, float] | None:
        terminal_positions = layout_map.get("terminal_positions", {})
        for stream_id, position in terminal_positions.items():
            if _node_has_stream(node, stream_id):
                return position
        node_positions = layout_map.get("node_positions", {})
        if node.node_id in node_positions:
            return node_positions[node.node_id]
        return None

    fallback_x, fallback_y = layout_map.get("fallback_origin", (120.0, 680.0))
    fallback_step_y = float(layout_map.get("fallback_step_y", 40.0))

    for node in nodes:
        position = _match_position(node)
        if position is not None:
            node.x, node.y = position
            continue
        if node.node_family == "terminal":
            node.x = fallback_x
            node.y = fallback_y
            fallback_y += node.height + fallback_step_y


def _pfd_stream_label(stream_id: str, description: str, stream_role: str) -> str:
    if stream_role in {"product", "waste", "vent", "purge", "recycle", "side_draw"}:
        return f"{stream_id}: {stream_role.replace('_', ' ').title()}"
    if description:
        short = description.split(".")[0].strip()
        return f"{stream_id}: {_truncate_with_ellipsis(short, 50)}"
    return stream_id


def _bac_stream_callout_rules() -> dict[str, dict[str, object]]:
    return {
        "S-150": {"label": "S-150: Reactor feed", "show_condition": True},
        "S-201": {"label": "S-201: Reactor effluent", "show_condition": True},
        "S-202": {"label": "S-202: Vent / purge", "show_condition": False},
        "S-203": {"label": "S-203: Rich liquid to cleanup", "show_condition": True},
        "S-301": {"label": "S-301: Recycle", "show_condition": False},
        "S-402": {"label": "S-402: Product", "show_condition": False},
        "S-403": {"label": "S-403: Waste", "show_condition": False},
        "S-404": {"label": "S-404: Side draw", "show_condition": False},
        "S-401": {"label": "S-401: Recycle return", "show_condition": False},
        "S-101": {"label": "S-101: Feed", "show_condition": False},
        "S-102": {"label": "S-102: Feed", "show_condition": False},
    }


def _bac_stream_callout(stream_id: str, description: str, stream_role: str) -> tuple[str, bool]:
    rule = _bac_stream_callout_rules().get(stream_id.upper())
    if rule is not None:
        return str(rule["label"]), bool(rule.get("show_condition", False))
    return _pfd_stream_label(stream_id, description, stream_role), stream_role == "main"


def _bac_service_label_map() -> dict[str, str]:
    return {
        "M-101": "Feed Prep Vessel",
        "R-101": "Jacketed CSTR",
        "V-101": "Primary Flash Drum",
        "E-101": "Cleanup Exchanger",
        "PU-201": "Purification Column",
        "TK-301": "Product Storage",
        "WT-401": "Waste Receiver",
    }


def _bac_service_label(text: str, equipment_tag: str) -> str:
    return _bac_service_label_map().get(equipment_tag.upper(), text)


def _bac_label_style(node: DiagramNode, label: DiagramLabel, index: int) -> dict[str, object]:
    if label.kind == "primary":
        return {
            "font_size": 15,
            "font_weight": "700",
            "wrap": 12,
            "line_gap": 12,
            "y": node.y + 22,
            "boxed": True,
            "fill": "#ffffff",
            "text": label.text,
        }
    if label.kind == "secondary":
        return {
            "font_size": 9,
            "font_weight": "400",
            "wrap": 18,
            "line_gap": 11,
            "y": node.y + 44,
            "boxed": False,
            "fill": "#ffffff",
            "text": _bac_service_label(label.text, node.equipment_tag),
        }
    return {
        "font_size": 8,
        "font_weight": "400",
        "wrap": 22,
        "line_gap": 10,
        "y": node.y + 59 + max(0, index - 2) * 13,
        "boxed": False,
        "fill": "#ffffff",
        "text": label.text,
    }


def _edge_type_from_role(stream_role: str) -> str:
    if stream_role in {"product", "recycle", "purge", "vent", "waste", "side_draw"}:
        return stream_role
    return "main"


def _bac_pfd_route_map() -> dict[str, dict[str, dict[str, object]]]:
    return {
        "PFD Sheet 1: Feed, Reaction, and Cleanup": {
            "S-150": {
                "points": [(536.0, 393.0), (598.0, 393.0), (598.0, 340.0), (716.0, 340.0)],
                "label": (598.0, 322.0),
                "condition": (598.0, 336.0),
            },
            "S-201": {
                "points": [(920.0, 340.0), (976.0, 340.0), (976.0, 308.0), (1058.0, 308.0)],
                "label": (976.0, 290.0),
                "condition": (976.0, 304.0),
            },
            "S-202": {
                "points": [(1071.0, 390.0), (1071.0, 250.0), (1450.0, 250.0), (1450.0, 130.0)],
                "label": (1265.0, 232.0),
                "condition": (1265.0, 246.0),
            },
            "S-203": {
                "points": [(1258.0, 344.0), (1348.0, 344.0), (1348.0, 338.0), (1480.0, 338.0)],
                "label": (1348.0, 320.0),
                "condition": (1348.0, 334.0),
            },
            "S-301": {
                "path": "M 1670.0 338.0 C 1744.0 228.0, 300.0 224.0, 338.0 393.0",
                "label": (1008.0, 212.0),
                "condition": (1008.0, 226.0),
            },
        },
        "PFD Sheet 2: Purification, Storage, and Offsites": {
            "S-402": {
                "points": [(414.0, 341.0), (596.0, 341.0), (596.0, 255.0), (828.0, 255.0)],
                "label": (596.0, 237.0),
                "condition": (596.0, 251.0),
            },
            "S-403": {
                "points": [(414.0, 341.0), (598.0, 341.0), (598.0, 550.0), (834.0, 550.0)],
                "label": (598.0, 323.0),
                "condition": (598.0, 337.0),
            },
        },
    }


def _path_from_points(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    segments = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for x, y in points[1:]:
        segments.append(f"L {x:.1f} {y:.1f}")
    return " ".join(segments)


def _bac_edge_route(sheet_title: str, edge_label: str | None) -> dict[str, object] | None:
    if not edge_label:
        return None
    stream_id = edge_label.split(":")[0].strip().upper()
    return _bac_pfd_route_map().get(sheet_title, {}).get(stream_id)


def _render_svg(
    sheet: DiagramSheet,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    style: DiagramStyleProfile,
    *,
    subtitle: str = "",
) -> str:
    node_lookup = {node.node_id: node for node in nodes}
    edge_color_map = {
        "main": style.stream_stroke,
        "product": "#2a7f3f",
        "recycle": style.recycle_stroke,
        "purge": "#8a5b2b",
        "vent": "#b36b00",
        "waste": "#a63d40",
        "side_draw": "#6d4c9b",
        "utility": style.utility_stroke,
    }
    defs = (
        "<defs>"
        + "".join(
            (
                f"<marker id='arrow-{edge_type}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'>"
                f"<path d='M 0 0 L 10 5 L 0 10 z' fill='{color}'/></marker>"
            )
            for edge_type, color in edge_color_map.items()
        )
        + "</defs>"
    )
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{sheet.width_px}' height='{sheet.height_px}' viewBox='0 0 {sheet.width_px} {sheet.height_px}'>",
        defs,
        f"<rect x='1' y='1' width='{sheet.width_px - 2}' height='{sheet.height_px - 2}' fill='white' stroke='#222' stroke-width='1.2'/>",
    ]
    if "pfd sheet" not in sheet.title.lower():
        parts.append(
            f"<text x='{sheet.width_px/2:.0f}' y='34' text-anchor='middle' font-family='{html.escape(style.heading_font_family)}' font-size='22' font-weight='700'>{html.escape(sheet.title)}</text>"
        )
    if subtitle and "pfd sheet" not in sheet.title.lower():
        parts.append(
            f"<text x='{sheet.width_px/2:.0f}' y='58' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='12'>{html.escape(subtitle)}</text>"
        )
    if "pfd sheet" in sheet.title.lower():
        parts.extend(_svg_pfd_sheet_frame(sheet.width_px, sheet.height_px, sheet.title, style))
        parts.extend(_svg_bac_section_zones(sheet))
    if "process flow diagram" in sheet.title.lower() or "pfd sheet" in sheet.title.lower():
        parts.extend(_svg_pfd_legend(sheet.width_px, style))

    for edge in edges:
        source = node_lookup.get(edge.source_node_id)
        target = node_lookup.get(edge.target_node_id)
        if source is None or target is None:
            continue
        line_color = edge_color_map.get(edge.edge_type, style.stream_stroke)
        marker = f"url(#arrow-{edge.edge_type if edge.edge_type in edge_color_map else 'main'})"
        stroke_dash = "8,6" if edge.edge_type in {"recycle", "purge", "vent", "waste", "side_draw"} else "none"
        x1, y1 = _node_connection_point(source, "right")
        x2, y2 = _node_connection_point(target, "left")
        manual_route = _bac_edge_route(sheet.title, edge.label) if "pfd sheet" in sheet.title.lower() else None
        if manual_route is not None:
            if "path" in manual_route:
                path = str(manual_route["path"])
            else:
                path = _path_from_points(list(manual_route.get("points", [])))
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x, label_y = manual_route.get("label", ((x1 + x2) / 2, min(y1, y2) - 8))
            condition_x, condition_y = manual_route.get("condition", (label_x, label_y + 14))
        elif edge.edge_type == "recycle":
            mid_y = min(source.y, target.y) - 48
            path = f"M {x1:.1f} {y1:.1f} C {x1+70:.1f} {mid_y:.1f}, {x2-70:.1f} {mid_y:.1f}, {x2:.1f} {y2:.1f}"
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x = (x1 + x2) / 2
            label_y = mid_y - 10
            condition_x = label_x
            condition_y = label_y + 14
        else:
            elbow_x = x1 + max(28.0, (x2 - x1) * 0.45)
            path = f"M {x1:.1f} {y1:.1f} L {elbow_x:.1f} {y1:.1f} L {elbow_x:.1f} {y2:.1f} L {x2:.1f} {y2:.1f}"
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x = elbow_x
            label_y = min(y1, y2) - 8
            condition_x = label_x
            condition_y = label_y + 14
        if edge.label:
            parts.extend(_svg_label_callout(label_x, label_y - 12, edge.label, style, wrap=28))
            parts.append(_svg_multiline_text(label_x, label_y, edge.label, style.body_font_family, 11, anchor="middle", wrap=28, line_gap=12))
        if edge.condition_label:
            parts.extend(_svg_label_callout(condition_x, condition_y - 12, edge.condition_label, style, wrap=24, font_size=9, fill="#fffef8"))
            parts.append(_svg_multiline_text(condition_x, condition_y, edge.condition_label, style.body_font_family, 9, anchor="middle", wrap=28, line_gap=10))

    for node in nodes:
        parts.extend(_svg_node_shape(node, style))
        for index, label in enumerate(node.labels[:3]):
            if "pfd sheet" in sheet.title.lower():
                label_style = _bac_label_style(node, label, index)
                font_size = int(label_style["font_size"])
                font_weight = str(label_style["font_weight"])
                wrap_width = int(label_style["wrap"])
                line_gap = int(label_style["line_gap"])
                text_y = float(label_style["y"])
                label_text = str(label_style["text"])
                if bool(label_style["boxed"]):
                    parts.extend(
                        _svg_label_callout(
                            node.x + node.width / 2,
                            text_y - 12,
                            label_text,
                            style,
                            wrap=wrap_width,
                            font_size=font_size,
                            fill="#ffffff",
                        )
                    )
            else:
                text_y = node.y + 24 + index * 16
                font_size = 13 if label.kind == "primary" else 10
                font_weight = "700" if label.kind == "primary" else "400"
                wrap_width = 16 if label.kind == "primary" else 24
                line_gap = 12
                label_text = label.text
                if label.kind == "utility":
                    font_size = 9
                    wrap_width = 26
            parts.append(
                _svg_multiline_text(
                    node.x + node.width / 2,
                    text_y,
                    label_text,
                    style.body_font_family,
                    font_size,
                    anchor="middle",
                    font_weight=font_weight,
                    wrap=wrap_width,
                    line_gap=line_gap,
                )
            )
    parts.append("</svg>")
    return "".join(parts)


def _build_instrumented_overlay_sheet(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    style: DiagramStyleProfile,
) -> DiagramSheet:
    unit_to_loops: dict[str, list] = {}
    for loop in control_plan.control_loops:
        if loop.unit_id:
            unit_to_loops.setdefault(loop.unit_id, []).append(loop)
    ordered_unit_ids = [unit_id for unit_id in control_architecture.critical_units if unit_id in unit_to_loops]
    ordered_unit_ids.extend(unit_id for unit_id in unit_to_loops if unit_id not in ordered_unit_ids)
    nodes: list[DiagramNode] = []
    family_guess = {
        "R-": "reactor",
        "PU-": "separator",
        "TK-": "tank",
        "P-": "pump",
        "E-": "heat exchanger",
        "D-": "column",
    }
    for rank, unit_id in enumerate(ordered_unit_ids):
        loop_ids = [loop.control_id for loop in unit_to_loops.get(unit_id, [])]
        node_family = "separator"
        for prefix, family in family_guess.items():
            if unit_id.upper().startswith(prefix):
                node_family = family
                break
        labels = [DiagramLabel(text=unit_id)]
        labels.append(DiagramLabel(text=", ".join(loop_ids[:2]), kind="secondary"))
        if len(loop_ids) > 2:
            labels.append(DiagramLabel(text=f"+{len(loop_ids) - 2} more loops", kind="utility"))
        nodes.append(
            DiagramNode(
                node_id=unit_id,
                label=unit_id,
                node_family=node_family,
                section_id="control_overlay",
                equipment_tag=unit_id,
                labels=labels,
                layout=DiagramLayoutHints(rank=rank),
            )
        )
    _layout_sheet_nodes(nodes, style, "Instrumented Process Flow Overlay")
    edges: list[DiagramEdge] = []
    edge_counter = 1
    for left, right in zip(nodes, nodes[1:]):
        edges.append(
            DiagramEdge(
                edge_id=f"overlay_edge_{edge_counter}",
                source_node_id=left.node_id,
                target_node_id=right.node_id,
                edge_type="main",
                stream_id="",
                label="Control interaction path",
                condition_label="",
                sheet_id="sheet_2",
            )
        )
        edge_counter += 1
    overlay_svg = _render_svg(
        DiagramSheet(
            sheet_id="sheet_2",
            title="Instrumented Process Flow Overlay",
            width_px=max(style.canvas_width_px, int(len(nodes) * 250 + 240)),
            height_px=max(style.canvas_height_px, 940),
            orientation="landscape",
            presentation_mode="sheet",
            preferred_scale=1.0,
            full_page=True,
            legend_mode="embedded",
            suppress_inline_wrapping=True,
            node_ids=[node.node_id for node in nodes],
            edge_ids=[edge.edge_id for edge in edges],
        ),
        nodes,
        edges,
        style,
        subtitle="Major process units with principal loop identifiers",
    )
    return DiagramSheet(
        sheet_id="sheet_2",
        title="Instrumented Process Flow Overlay",
        width_px=max(style.canvas_width_px, int(len(nodes) * 250 + 240)),
        height_px=max(style.canvas_height_px, 940),
        orientation="landscape",
        presentation_mode="sheet",
        preferred_scale=1.0,
        full_page=True,
        legend_mode="embedded",
        suppress_inline_wrapping=True,
        node_ids=[node.node_id for node in nodes],
        edge_ids=[edge.edge_id for edge in edges],
        svg=overlay_svg,
    )


def _render_control_system_svg(
    width_px: int,
    height_px: int,
    *,
    title: str,
    subtitle: str,
    unit_ids: list[str],
    loop_groups: dict[str, list],
    unit_label_by_id: dict[str, str],
    style: DiagramStyleProfile,
) -> str:
    x_margin = 70
    unit_y = 110
    loop_y = 300
    dcs_y = 560
    spacing = (width_px - 2 * x_margin) / max(1, len(unit_ids))
    dcs_width = min(520, width_px - 220)
    dcs_x = (width_px - dcs_width) / 2
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width_px}' height='{height_px}' viewBox='0 0 {width_px} {height_px}'>",
        f"<rect x='1' y='1' width='{width_px - 2}' height='{height_px - 2}' fill='white' stroke='#222' stroke-width='1.2'/>",
        f"<text x='{width_px/2:.0f}' y='34' text-anchor='middle' font-family='{html.escape(style.heading_font_family)}' font-size='22' font-weight='700'>{html.escape(title)}</text>",
        f"<text x='{width_px/2:.0f}' y='58' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='12'>{html.escape(subtitle)}</text>",
        "<rect x='58' y='72' width='230' height='50' rx='6' ry='6' fill='#f6f7fb' stroke='#56657a' stroke-width='1.2'/>",
        f"<text x='173' y='93' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='12' font-weight='700'>Legend</text>",
        f"<text x='80' y='112' font-family='{html.escape(style.body_font_family)}' font-size='10'>Red border: high-criticality loop</text>",
    ]
    for index, unit_id in enumerate(unit_ids):
        loops = loop_groups.get(unit_id, [])
        x_center = x_margin + spacing * index + spacing / 2
        unit_width = min(190, spacing - 24)
        unit_x = x_center - unit_width / 2
        unit_label = _display_equipment_label(unit_label_by_id.get(unit_id) or unit_id)
        parts.append(
            f"<rect x='{unit_x:.1f}' y='{unit_y:.1f}' width='{unit_width:.1f}' height='72' rx='8' ry='8' fill='#f7f7f7' stroke='{style.node_stroke}' stroke-width='1.5'/>"
        )
        parts.append(_svg_multiline_text(x_center, unit_y + 24, unit_label, style.body_font_family, 12, anchor="middle", font_weight="700", wrap=18, line_gap=12))
        parts.append(_svg_multiline_text(x_center, unit_y + 49, unit_id, style.body_font_family, 10, anchor="middle", wrap=20, line_gap=11))
        loop_box_y = loop_y
        for loop in loops[:4]:
            critical_color = "#a63d40" if (loop.criticality or "").lower() == "high" else "#456b9a"
            parts.append(
                f"<line x1='{x_center:.1f}' y1='{unit_y + 72:.1f}' x2='{x_center:.1f}' y2='{loop_box_y:.1f}' stroke='#7b8794' stroke-width='1.2'/>"
            )
            parts.append(
                f"<rect x='{x_center - 78:.1f}' y='{loop_box_y:.1f}' width='156' height='44' rx='10' ry='10' fill='#ffffff' stroke='{critical_color}' stroke-width='1.5'/>"
            )
            parts.append(_svg_multiline_text(x_center, loop_box_y + 18, loop.control_id, style.body_font_family, 11, anchor="middle", font_weight="700", wrap=20, line_gap=11))
            parts.append(_svg_multiline_text(x_center, loop_box_y + 32, _truncate_with_ellipsis(loop.controlled_variable, 30), style.body_font_family, 9, anchor="middle", wrap=24, line_gap=10))
            parts.append(
                f"<line x1='{x_center:.1f}' y1='{loop_box_y + 44:.1f}' x2='{width_px / 2:.1f}' y2='{dcs_y:.1f}' stroke='#9aa5b1' stroke-width='1.0' stroke-dasharray='5,4'/>"
            )
            loop_box_y += 60
    parts.append(
        f"<rect x='{dcs_x:.1f}' y='{dcs_y:.1f}' width='{dcs_width:.1f}' height='72' rx='10' ry='10' fill='#eef3fb' stroke='#38588a' stroke-width='1.6'/>"
    )
    parts.append(_svg_multiline_text(width_px / 2, dcs_y + 27, subtitle, style.body_font_family, 14, anchor="middle", font_weight="700", wrap=40, line_gap=14))
    parts.append(_svg_multiline_text(width_px / 2, dcs_y + 49, "Supervisory control, alarms, interlocks, and operator interface", style.body_font_family, 10, anchor="middle", wrap=52, line_gap=11))
    parts.append("</svg>")
    return "".join(parts)


def _mermaid_from_diagram(nodes: list[DiagramNode], edges: list[DiagramEdge], *, orientation: str = "LR") -> str:
    lines = [f"flowchart {orientation}"]
    for node in nodes:
        lines.append(f'  {node.node_id}["{node.label}"]')
    for edge in edges:
        arrow = "-.->" if edge.edge_type == "recycle" else "-->"
        lines.append(f"  {edge.source_node_id} {arrow} {edge.target_node_id}")
    return "\n".join(lines)


def _truncate_with_ellipsis(text: str, max_len: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_len:
        return compact
    return compact[: max(0, max_len - 1)].rstrip() + "…"


def _display_equipment_label(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if re.fullmatch(r"[A-Za-z]{1,4}-\d{2,4}", compact):
        return compact.upper()
    words = []
    for token in compact.split(" "):
        if re.fullmatch(r"[A-Za-z]{1,4}-\d{2,4}", token):
            words.append(token.upper())
        else:
            words.append(token.capitalize())
    return " ".join(words)


def _control_loop_ids_for_node(node: DiagramNode, equipment_id: str, loops_by_unit: dict[str, list[str]]) -> list[str]:
    loop_ids: list[str] = []
    for key in filter(None, [node.node_id, equipment_id]):
        for loop_id in loops_by_unit.get(key, []):
            if loop_id not in loop_ids:
                loop_ids.append(loop_id)
    if loop_ids:
        return loop_ids
    lowered = f"{node.label} {node.node_id} {equipment_id}".lower()
    heuristic_units: list[str] = []
    if any(token in lowered for token in ("reaction", "reactor", "quaternization")):
        heuristic_units.append("R-101")
    if any(token in lowered for token in ("purification", "distillation", "separation", "flash")):
        heuristic_units.append("PU-201")
    if any(token in lowered for token in ("storage", "tank", "dispatch")):
        heuristic_units.append("TK-301")
    for unit_id in heuristic_units:
        for loop_id in loops_by_unit.get(unit_id, []):
            if loop_id not in loop_ids:
                loop_ids.append(loop_id)
    return loop_ids


def _wrap_text_lines(text: str, wrap: int) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return []
    words = compact.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= wrap:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines[:3]


def _svg_multiline_text(
    x: float,
    y: float,
    text: str,
    font_family: str,
    font_size: int,
    *,
    anchor: str = "start",
    font_weight: str = "400",
    wrap: int = 24,
    line_gap: int = 12,
) -> str:
    lines = _wrap_text_lines(text, wrap)
    if not lines:
        return ""
    escaped_family = html.escape(font_family)
    tspans = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else str(line_gap)
        tspans.append(f"<tspan x='{x:.1f}' dy='{dy}'>{html.escape(line)}</tspan>")
    return (
        f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='{anchor}' font-family='{escaped_family}' "
        f"font-size='{font_size}' font-weight='{font_weight}'>" + "".join(tspans) + "</text>"
    )


def _node_connection_point(node: DiagramNode, side: str) -> tuple[float, float]:
    cx = node.x + node.width / 2
    cy = node.y + node.height / 2
    if node.node_family in {"column", "bac_purification_column"}:
        rect_width = max(100.0, node.width * 0.68)
        rect_x = node.x + (node.width - rect_width) / 2
        return (rect_x + rect_width + 10.0, cy) if side == "right" else (rect_x - 10.0, cy)
    if node.node_family == "bac_exchanger_package":
        return (node.x + node.width - 20.0, cy) if side == "right" else (node.x + 20.0, cy)
    if node.node_family == "bac_flash_drum":
        y_offset = -18.0 if side == "left" else 18.0
        return (node.x + node.width - 10.0, cy + y_offset) if side == "right" else (node.x + 10.0, cy + y_offset)
    if node.node_family in {"bac_reactor", "bac_premix_vessel", "bac_storage_tank", "bac_waste_receiver", "reactor", "tank", "vessel", "separator"}:
        return (node.x + node.width - 8.0, cy) if side == "right" else (node.x + 8.0, cy)
    if node.node_family in {"heat exchanger", "condenser"}:
        return (node.x + node.width - 18.0, cy) if side == "right" else (node.x + 18.0, cy)
    if node.node_family == "pump":
        return (node.x + node.width - 12.0, cy) if side == "right" else (node.x + 10.0, cy)
    if node.node_family == "compressor":
        return (node.x + node.width - 12.0, cy) if side == "right" else (node.x + 12.0, cy)
    return (node.x + node.width, cy) if side == "right" else (node.x, cy)


def _svg_node_shape(node: DiagramNode, style: DiagramStyleProfile) -> list[str]:
    x = node.x
    y = node.y
    w = node.width
    h = node.height
    cy = y + h / 2
    stroke = style.node_stroke
    fill = style.node_fill
    if node.node_family == "bac_purification_column":
        rect_width = max(110.0, w * 0.64)
        rect_x = x + (w - rect_width) / 2
        tray_positions = [y + 34, y + 70, y + 106, y + 142]
        parts = [
            f"<rect x='{rect_x:.1f}' y='{y + 8:.1f}' width='{rect_width:.1f}' height='{h - 16:.1f}' rx='34' ry='34' fill='{fill}' stroke='{stroke}' stroke-width='1.7'/>",
            f"<line x1='{rect_x + rect_width/2:.1f}' y1='{y + 18:.1f}' x2='{rect_x + rect_width/2:.1f}' y2='{y + h - 18:.1f}' stroke='#9aa5b1' stroke-width='0.9' stroke-dasharray='4,3'/>",
            f"<line x1='{rect_x - 14:.1f}' y1='{y + 36:.1f}' x2='{rect_x + 8:.1f}' y2='{y + 36:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{rect_x + rect_width - 8:.1f}' y1='{y + 52:.1f}' x2='{rect_x + rect_width + 18:.1f}' y2='{y + 52:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{rect_x + rect_width - 8:.1f}' y1='{y + h - 36:.1f}' x2='{rect_x + rect_width + 18:.1f}' y2='{y + h - 36:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{rect_x - 14:.1f}' y1='{y + h - 54:.1f}' x2='{rect_x + 8:.1f}' y2='{y + h - 54:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
        ]
        for tray_y in tray_positions:
            parts.append(f"<line x1='{rect_x + 18:.1f}' y1='{tray_y:.1f}' x2='{rect_x + rect_width - 18:.1f}' y2='{tray_y:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>")
        return parts
    if node.node_family == "column":
        rect_width = max(100.0, w * 0.68)
        rect_x = x + (w - rect_width) / 2
        return [
            f"<rect x='{rect_x:.1f}' y='{y:.1f}' width='{rect_width:.1f}' height='{h:.1f}' rx='34' ry='34' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{rect_x + rect_width/2:.1f}' y1='{y + 10:.1f}' x2='{rect_x + rect_width/2:.1f}' y2='{y + h - 10:.1f}' stroke='#9aa5b1' stroke-width='1.0' stroke-dasharray='4,3'/>",
            f"<line x1='{rect_x + 18:.1f}' y1='{y + 18:.1f}' x2='{rect_x + rect_width - 18:.1f}' y2='{y + 18:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>",
            f"<line x1='{rect_x + 18:.1f}' y1='{y + h - 18:.1f}' x2='{rect_x + rect_width - 18:.1f}' y2='{y + h - 18:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>",
            f"<line x1='{rect_x - 10:.1f}' y1='{y + 24:.1f}' x2='{rect_x + 8:.1f}' y2='{y + 24:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{rect_x + rect_width - 8:.1f}' y1='{y + h - 24:.1f}' x2='{rect_x + rect_width + 10:.1f}' y2='{y + h - 24:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{rect_x + rect_width - 8:.1f}' y1='{y + 24:.1f}' x2='{rect_x + rect_width + 10:.1f}' y2='{y + 24:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{rect_x - 10:.1f}' y1='{y + h - 24:.1f}' x2='{rect_x + 8:.1f}' y2='{y + h - 24:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
        ]
    if node.node_family == "bac_reactor":
        shell_x = x + 22
        shell_w = w - 44
        return [
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + 18:.1f}' rx='{shell_w/2:.1f}' ry='18' fill='{fill}' stroke='{stroke}' stroke-width='1.9'/>",
            f"<rect x='{shell_x:.1f}' y='{y + 18:.1f}' width='{shell_w:.1f}' height='{h - 36:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.9'/>",
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + h - 18:.1f}' rx='{shell_w/2:.1f}' ry='18' fill='{fill}' stroke='{stroke}' stroke-width='1.9'/>",
            f"<rect x='{shell_x - 8:.1f}' y='{y + 28:.1f}' width='{shell_w + 16:.1f}' height='{h - 56:.1f}' rx='26' ry='26' fill='none' stroke='#5b84b1' stroke-width='1.0' stroke-dasharray='5,4'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y - 16:.1f}' x2='{x + w/2:.1f}' y2='{y + 30:.1f}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<circle cx='{x + w/2:.1f}' cy='{y + 42:.1f}' r='15' fill='white' stroke='#7b8794' stroke-width='1.0'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 42:.1f}' x2='{x + w/2 + 24:.1f}' y2='{y + 58:.1f}' stroke='#7b8794' stroke-width='1.1'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 42:.1f}' x2='{x + w/2 - 22:.1f}' y2='{y + 58:.1f}' stroke='#7b8794' stroke-width='1.1'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 42:.1f}' x2='{x + w/2:.1f}' y2='{y + 64:.1f}' stroke='#7b8794' stroke-width='1.1'/>",
            f"<line x1='{x + 6:.1f}' y1='{cy:.1f}' x2='{x + 22:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.4'/>",
            f"<line x1='{x + w - 22:.1f}' y1='{cy:.1f}' x2='{x + w - 6:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.4'/>",
            f"<line x1='{x + w/2 - 22:.1f}' y1='{y - 4:.1f}' x2='{x + w/2 - 4:.1f}' y2='{y - 4:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{x + w/2 + 4:.1f}' y1='{y - 4:.1f}' x2='{x + w/2 + 22:.1f}' y2='{y - 4:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
        ]
    if node.node_family == "reactor":
        return [
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + 16:.1f}' rx='{(w - 34)/2:.1f}' ry='16' fill='{fill}' stroke='{stroke}' stroke-width='1.8'/>",
            f"<rect x='{x + 18:.1f}' y='{y + 16:.1f}' width='{w - 36:.1f}' height='{h - 32:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.8'/>",
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + h - 16:.1f}' rx='{(w - 34)/2:.1f}' ry='16' fill='{fill}' stroke='{stroke}' stroke-width='1.8'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y - 8:.1f}' x2='{x + w/2:.1f}' y2='{y + 24:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<circle cx='{x + w/2:.1f}' cy='{y + 36:.1f}' r='14' fill='white' stroke='#7b8794' stroke-width='1.0'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 36:.1f}' x2='{x + w/2 + 20:.1f}' y2='{y + 50:.1f}' stroke='#7b8794' stroke-width='1.0'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 36:.1f}' x2='{x + w/2 - 18:.1f}' y2='{y + 50:.1f}' stroke='#7b8794' stroke-width='1.0'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 36:.1f}' x2='{x + w/2:.1f}' y2='{y + 56:.1f}' stroke='#7b8794' stroke-width='1.0'/>",
            f"<line x1='{x + 8:.1f}' y1='{cy:.1f}' x2='{x + 20:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 20:.1f}' y1='{cy:.1f}' x2='{x + w - 8:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "compressor":
        return [
            f"<polygon points='{x + 18:.1f},{y + 16:.1f} {x + w - 30:.1f},{y + 16:.1f} {x + w - 12:.1f},{y + h/2:.1f} {x + w - 30:.1f},{y + h - 16:.1f} {x + 18:.1f},{y + h - 16:.1f} {x + 40:.1f},{y + h/2:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{x + 46:.1f}' y1='{y + 24:.1f}' x2='{x + w - 48:.1f}' y2='{y + 24:.1f}' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<line x1='{x + 46:.1f}' y1='{y + h - 24:.1f}' x2='{x + w - 48:.1f}' y2='{y + h - 24:.1f}' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<polyline points='{x + 55:.1f},{y + h/2:.1f} {x + 78:.1f},{y + 28:.1f} {x + 78:.1f},{y + h - 28:.1f}' fill='none' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<polyline points='{x + 95:.1f},{y + h/2:.1f} {x + 118:.1f},{y + 28:.1f} {x + 118:.1f},{y + h - 28:.1f}' fill='none' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<line x1='{x + 4:.1f}' y1='{cy:.1f}' x2='{x + 20:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 16:.1f}' y1='{cy:.1f}' x2='{x + w - 2:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "heat exchanger":
        return [
            f"<rect x='{x + 20:.1f}' y='{y + 20:.1f}' width='{w - 40:.1f}' height='{h - 40:.1f}' rx='28' ry='28' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{x + 42:.1f}' y1='{y + h/2:.1f}' x2='{x + w - 42:.1f}' y2='{y + h/2:.1f}' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<line x1='{x + 56:.1f}' y1='{y + 30:.1f}' x2='{x + 56:.1f}' y2='{y + h - 30:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>",
            f"<line x1='{x + w - 56:.1f}' y1='{y + 30:.1f}' x2='{x + w - 56:.1f}' y2='{y + h - 30:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>",
            f"<line x1='{x + 6:.1f}' y1='{cy:.1f}' x2='{x + 22:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 22:.1f}' y1='{cy:.1f}' x2='{x + w - 6:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "bac_exchanger_package":
        body_x = x + 18
        body_y = y + 24
        body_w = w - 36
        body_h = h - 48
        return [
            f"<rect x='{body_x:.1f}' y='{body_y:.1f}' width='{body_w:.1f}' height='{body_h:.1f}' rx='28' ry='28' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{body_x + 20:.1f}' y1='{cy:.1f}' x2='{body_x + body_w - 20:.1f}' y2='{cy:.1f}' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<line x1='{body_x + 48:.1f}' y1='{body_y + 10:.1f}' x2='{body_x + 48:.1f}' y2='{body_y + body_h - 10:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>",
            f"<line x1='{body_x + body_w - 48:.1f}' y1='{body_y + 10:.1f}' x2='{body_x + body_w - 48:.1f}' y2='{body_y + body_h - 10:.1f}' stroke='#9aa5b1' stroke-width='0.9'/>",
            f"<circle cx='{body_x + body_w - 58:.1f}' cy='{body_y + 24:.1f}' r='7' fill='white' stroke='#5b84b1' stroke-width='1.0'/>",
            f"<circle cx='{body_x + body_w - 58:.1f}' cy='{body_y + body_h - 24:.1f}' r='7' fill='white' stroke='#5b84b1' stroke-width='1.0'/>",
            f"<line x1='{x + 4:.1f}' y1='{cy:.1f}' x2='{body_x:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{body_x + body_w:.1f}' y1='{cy:.1f}' x2='{x + w - 4:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "condenser":
        return [
            f"<rect x='{x + 20:.1f}' y='{y + 20:.1f}' width='{w - 40:.1f}' height='{h - 40:.1f}' rx='28' ry='28' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{x + 42:.1f}' y1='{y + h/2:.1f}' x2='{x + w - 42:.1f}' y2='{y + h/2:.1f}' stroke='#9aa5b1' stroke-width='1.0'/>",
            f"<path d='M {x + w - 62:.1f} {y + 30:.1f} q 10 10 0 20 q -10 10 0 20 q 10 10 0 20' fill='none' stroke='#7da8d8' stroke-width='1.2'/>",
            f"<path d='M {x + w - 48:.1f} {y + 30:.1f} q 10 10 0 20 q -10 10 0 20 q 10 10 0 20' fill='none' stroke='#7da8d8' stroke-width='1.2'/>",
            f"<line x1='{x + 6:.1f}' y1='{cy:.1f}' x2='{x + 22:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 22:.1f}' y1='{cy:.1f}' x2='{x + w - 6:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "pump":
        return [
            f"<line x1='{x + 10:.1f}' y1='{y + h/2:.1f}' x2='{x + 42:.1f}' y2='{y + h/2:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<circle cx='{x + 74:.1f}' cy='{y + h/2:.1f}' r='28' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<polygon points='{x + 64:.1f},{y + h/2 - 12:.1f} {x + 90:.1f},{y + h/2:.1f} {x + 64:.1f},{y + h/2 + 12:.1f}' fill='#9aa5b1' stroke='none'/>",
            f"<line x1='{x + 102:.1f}' y1='{y + h/2:.1f}' x2='{x + w - 12:.1f}' y2='{y + h/2:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "bac_premix_vessel":
        return [
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + 14:.1f}' rx='{(w - 30)/2:.1f}' ry='14' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<rect x='{x + 15:.1f}' y='{y + 14:.1f}' width='{w - 30:.1f}' height='{h - 28:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + h - 14:.1f}' rx='{(w - 30)/2:.1f}' ry='14' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y - 10:.1f}' x2='{x + w/2:.1f}' y2='{y + 24:.1f}' stroke='{stroke}' stroke-width='1.1'/>",
            f"<circle cx='{x + w/2:.1f}' cy='{y + 36:.1f}' r='11' fill='white' stroke='#7b8794' stroke-width='0.9'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 36:.1f}' x2='{x + w/2 + 16:.1f}' y2='{y + 46:.1f}' stroke='#7b8794' stroke-width='0.9'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 36:.1f}' x2='{x + w/2 - 14:.1f}' y2='{y + 46:.1f}' stroke='#7b8794' stroke-width='0.9'/>",
            f"<line x1='{x + 5:.1f}' y1='{cy:.1f}' x2='{x + 16:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{x + w - 16:.1f}' y1='{cy:.1f}' x2='{x + w - 5:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
        ]
    if node.node_family == "bac_storage_tank":
        return [
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + 12:.1f}' rx='{(w - 28)/2:.1f}' ry='12' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<rect x='{x + 14:.1f}' y='{y + 12:.1f}' width='{w - 28:.1f}' height='{h - 24:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + h - 12:.1f}' rx='{(w - 28)/2:.1f}' ry='12' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{x + 4:.1f}' y1='{cy:.1f}' x2='{x + 16:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 16:.1f}' y1='{cy:.1f}' x2='{x + w - 4:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y - 6:.1f}' x2='{x + w/2:.1f}' y2='{y + 10:.1f}' stroke='{stroke}' stroke-width='1.1'/>",
        ]
    if node.node_family == "tank":
        return [
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + 10:.1f}' rx='{(w - 28)/2:.1f}' ry='10' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<rect x='{x + 14:.1f}' y='{y + 10:.1f}' width='{w - 28:.1f}' height='{h - 20:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + h - 10:.1f}' rx='{(w - 28)/2:.1f}' ry='10' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{x + 4:.1f}' y1='{cy:.1f}' x2='{x + 16:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 16:.1f}' y1='{cy:.1f}' x2='{x + w - 4:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "bac_flash_drum":
        return [
            f"<ellipse cx='{x + 26:.1f}' cy='{cy:.1f}' rx='26' ry='{(h - 24)/2:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<rect x='{x + 26:.1f}' y='{y + 12:.1f}' width='{w - 52:.1f}' height='{h - 24:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<ellipse cx='{x + w - 26:.1f}' cy='{cy:.1f}' rx='26' ry='{(h - 24)/2:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{x + 36:.1f}' y1='{cy:.1f}' x2='{x + w - 36:.1f}' y2='{cy:.1f}' stroke='#9aa5b1' stroke-width='1.0' stroke-dasharray='4,3'/>",
            f"<line x1='{x + 8:.1f}' y1='{cy - 18:.1f}' x2='{x + 28:.1f}' y2='{cy - 18:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{x + w - 28:.1f}' y1='{cy + 18:.1f}' x2='{x + w - 8:.1f}' y2='{cy + 18:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y - 10:.1f}' x2='{x + w/2:.1f}' y2='{y + 12:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + h - 12:.1f}' x2='{x + w/2:.1f}' y2='{y + h + 10:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
        ]
    if node.node_family == "bac_waste_receiver":
        return [
            f"<rect x='{x + 12:.1f}' y='{y + 12:.1f}' width='{w - 24:.1f}' height='{h - 24:.1f}' rx='28' ry='28' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{x + 22:.1f}' y1='{cy:.1f}' x2='{x + w - 22:.1f}' y2='{cy:.1f}' stroke='#9aa5b1' stroke-width='1.0' stroke-dasharray='4,3'/>",
            f"<line x1='{x + 4:.1f}' y1='{cy:.1f}' x2='{x + 18:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 18:.1f}' y1='{cy:.1f}' x2='{x + w - 4:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family in {"vessel", "separator"}:
        return [
            f"<rect x='{x + 10:.1f}' y='{y + 10:.1f}' width='{w - 20:.1f}' height='{h - 20:.1f}' rx='24' ry='24' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{x + 22:.1f}' y1='{y + h/2:.1f}' x2='{x + w - 22:.1f}' y2='{y + h/2:.1f}' stroke='#9aa5b1' stroke-width='1.0' stroke-dasharray='4,3'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 18:.1f}' x2='{x + w/2:.1f}' y2='{y + h - 18:.1f}' stroke='#d0d7de' stroke-width='0.8' stroke-dasharray='3,4'/>",
            f"<line x1='{x + 4:.1f}' y1='{cy:.1f}' x2='{x + 16:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
            f"<line x1='{x + w - 16:.1f}' y1='{cy:.1f}' x2='{x + w - 4:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.3'/>",
        ]
    if node.node_family == "terminal":
        return [
            f"<rect x='{x + 18:.1f}' y='{y + 16:.1f}' width='{w - 36:.1f}' height='{h - 32:.1f}' rx='6' ry='6' fill='#fbfbfb' stroke='{stroke}' stroke-width='1.3' stroke-dasharray='6,4'/>"
        ]
    return [f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' rx='8' ry='8' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>"]


def _svg_pfd_legend(width_px: int, style: DiagramStyleProfile) -> list[str]:
    x = 72
    y = 118
    items = [
        ("Main process stream", style.stream_stroke, "none"),
        ("Product stream", "#2a7f3f", "none"),
        ("Vent / purge / waste", "#a63d40", "8,6"),
        ("Recycle stream", style.recycle_stroke, "8,6"),
    ]
    parts = [
        f"<rect x='{x}' y='{y}' width='310' height='170' rx='0' ry='0' fill='#fdfefe' stroke='#56606b' stroke-width='1.0'/>",
        f"<line x1='{x}' y1='{y + 24}' x2='{x + 310}' y2='{y + 24}' stroke='#56606b' stroke-width='1.0'/>",
        f"<text x='{x + 155}' y='{y + 17}' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='11' font-weight='700'>LEGEND AND NOTATION</text>",
    ]
    for index, (label, color, dash) in enumerate(items):
        y0 = y + 42 + index * 18
        dash_attr = f" stroke-dasharray='{dash}'" if dash != "none" else ""
        parts.append(f"<line x1='{x + 16}' y1='{y0}' x2='{x + 62}' y2='{y0}' stroke='{color}' stroke-width='2.4'{dash_attr}/>")
        parts.append(f"<text x='{x + 72}' y='{y0 + 4}' font-family='{html.escape(style.body_font_family)}' font-size='10.5'>{html.escape(label)}</text>")
    parts.append(f"<text x='{x + 16}' y='{y + 125}' font-family='{html.escape(style.body_font_family)}' font-size='10.2' font-weight='700'>Notation</text>")
    parts.append(f"<text x='{x + 16}' y='{y + 141}' font-family='{html.escape(style.body_font_family)}' font-size='9.3'>Primary label: equipment tag</text>")
    parts.append(f"<text x='{x + 16}' y='{y + 154}' font-family='{html.escape(style.body_font_family)}' font-size='9.3'>Secondary label: service description</text>")
    parts.append(f"<text x='{x + 16}' y='{y + 167}' font-family='{html.escape(style.body_font_family)}' font-size='9.3'>Major process lines labeled by stream number</text>")
    return parts


def _svg_pfd_sheet_frame(width_px: int, height_px: int, title: str, style: DiagramStyleProfile) -> list[str]:
    title_x = 52
    title_y = 42
    frame_x = 38
    frame_y = 38
    frame_w = width_px - 76
    frame_h = height_px - 76
    title_band_h = 54
    info_x = width_px - 468
    info_y = height_px - 134
    parts = [
        f"<rect x='{frame_x}' y='{frame_y}' width='{frame_w}' height='{frame_h}' fill='none' stroke='#222' stroke-width='1.0'/>",
        f"<rect x='{frame_x + 10}' y='{frame_y + 10}' width='{frame_w - 20}' height='{frame_h - 20}' fill='none' stroke='#7f8a96' stroke-width='0.8'/>",
        f"<rect x='{frame_x + 10}' y='{frame_y + 10}' width='{frame_w - 20}' height='{title_band_h}' fill='#f7f9fc' stroke='#7f8a96' stroke-width='0.8'/>",
        f"<line x1='{frame_x + 10}' y1='{frame_y + 10 + title_band_h}' x2='{frame_x + frame_w - 10}' y2='{frame_y + 10 + title_band_h}' stroke='#7f8a96' stroke-width='0.8'/>",
        f"<rect x='{frame_x + 22}' y='{frame_y + 86}' width='{frame_w - 44}' height='{frame_h - 210}' fill='none' stroke='#d8dde5' stroke-width='0.7'/>",
        f"<text x='{title_x}' y='{title_y}' font-family='{html.escape(style.heading_font_family)}' font-size='17' font-weight='700'>PROCESS FLOW DIAGRAM</text>",
        f"<text x='{title_x}' y='{title_y + 20}' font-family='{html.escape(style.body_font_family)}' font-size='11.5'>{html.escape(title)}</text>",
        f"<text x='{title_x + 520}' y='{title_y}' font-family='{html.escape(style.body_font_family)}' font-size='10.2' font-weight='700'>Project: Benzalkonium Chloride</text>",
        f"<text x='{title_x + 520}' y='{title_y + 18}' font-family='{html.escape(style.body_font_family)}' font-size='9.4'>Sheet type: Full-page landscape drawing sheet</text>",
        f"<text x='{title_x + 520}' y='{title_y + 34}' font-family='{html.escape(style.body_font_family)}' font-size='9.4'>Equipment tags primary, stream numbers shown on major lines</text>",
        f"<rect x='{info_x}' y='{info_y}' width='420' height='96' rx='0' ry='0' fill='#ffffff' stroke='#222' stroke-width='1.0'/>",
        f"<line x1='{info_x}' y1='{info_y + 28}' x2='{info_x + 420}' y2='{info_y + 28}' stroke='#222' stroke-width='1.0'/>",
        f"<line x1='{info_x + 296}' y1='{info_y}' x2='{info_x + 296}' y2='{info_y + 96}' stroke='#222' stroke-width='1.0'/>",
        f"<text x='{info_x + 12}' y='{info_y + 18}' font-family='{html.escape(style.body_font_family)}' font-size='11' font-weight='700'>DRAWING NOTES</text>",
        f"<text x='{info_x + 12}' y='{info_y + 46}' font-family='{html.escape(style.body_font_family)}' font-size='9.5'>1. Process representation only</text>",
        f"<text x='{info_x + 12}' y='{info_y + 62}' font-family='{html.escape(style.body_font_family)}' font-size='9.5'>2. Major streams labeled by stream number</text>",
        f"<text x='{info_x + 12}' y='{info_y + 78}' font-family='{html.escape(style.body_font_family)}' font-size='9.5'>3. Equipment tags shown above service labels</text>",
        f"<text x='{info_x + 312}' y='{info_y + 18}' font-family='{html.escape(style.body_font_family)}' font-size='9.6' font-weight='700'>BAC</text>",
        f"<text x='{info_x + 312}' y='{info_y + 38}' font-family='{html.escape(style.body_font_family)}' font-size='9'>Orientation: Landscape</text>",
        f"<text x='{info_x + 312}' y='{info_y + 56}' font-family='{html.escape(style.body_font_family)}' font-size='9'>Scale: Report fit</text>",
        f"<text x='{info_x + 312}' y='{info_y + 74}' font-family='{html.escape(style.body_font_family)}' font-size='9'>Status: Drafted sheet</text>",
    ]
    return parts


def _svg_bac_section_zones(sheet: DiagramSheet) -> list[str]:
    title = sheet.title.lower()
    if "feed, reaction, and cleanup" in title:
        zones = [
            (60, 120, 220, 390, "#f3f6fb", "Feed"),
            (560, 120, 320, 390, "#f8f5ef", "Reaction"),
            (940, 120, 300, 390, "#f7f3fb", "Primary Recovery"),
            (1360, 120, 470, 390, "#f2f7f0", "Cleanup / Concentration"),
        ]
    elif "purification, storage, and offsites" in title:
        zones = [
            (180, 120, 420, 410, "#f7f3fb", "Purification"),
            (680, 120, 380, 260, "#f2f7f0", "Storage"),
            (680, 430, 380, 260, "#fbf2f0", "Waste / Offsites"),
            (1120, 120, 380, 600, "#f9f9f9", "Battery Limits"),
        ]
    else:
        return []
    parts: list[str] = []
    for x, y, w, h, fill, label in zones:
        parts.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='{fill}' stroke='#d7dde5' stroke-width='0.8'/>")
        parts.append(f"<text x='{x + 12}' y='{y + 18}' font-family='Calibri' font-size='11' font-weight='700' fill='#51606f'>{html.escape(label)}</text>")
    return parts


def _svg_label_callout(
    x: float,
    y: float,
    text: str,
    style: DiagramStyleProfile,
    *,
    wrap: int,
    font_size: int = 11,
    fill: str = "#ffffff",
) -> list[str]:
    lines = _wrap_text_lines(text, wrap)
    if not lines:
        return []
    width = min(300, max(78, max(len(line) for line in lines) * (font_size * 0.58) + 18))
    height = max(20, len(lines) * (font_size + 2) + 8)
    return [
        f"<rect x='{x - width/2:.1f}' y='{y - 10:.1f}' width='{width:.1f}' height='{height:.1f}' rx='4' ry='4' fill='{fill}' stroke='#d0d7de' stroke-width='0.8'/>"
    ]
