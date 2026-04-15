from __future__ import annotations

import html
import re

from aoc.models import (
    BACDrawingPackageArtifact,
    BACDrawingRegisterRow,
    BACDiagramBenchmarkArtifact,
    BACDiagramBenchmarkRow,
    BACRenderingAuditArtifact,
    BACRenderingAuditRow,
    BlockFlowDiagramArtifact,
    ControlArchitectureDecision,
    ControlCauseEffectArtifact,
    ControlCauseEffectRow,
    ControlPlanArtifact,
    ControlSystemDiagramArtifact,
    DiagramAcceptanceArtifact,
    DiagramEdge,
    DiagramEdgeRole,
    DiagramEdgeStyleRule,
    DiagramDomainPack,
    DiagramDomainPackArtifact,
    DiagramEquipmentPortTemplate,
    DiagramEquipmentTemplate,
    DiagramEquipmentTemplateArtifact,
    DiagramEntityKind,
    DiagramLabel,
    DiagramLayoutHints,
    DiagramLevel,
    DiagramLevelStylePolicy,
    DiagramModuleArtifact,
    DiagramModuleConstraint,
    DiagramInterModuleConnector,
    DiagramModulePlacement,
    DiagramModulePort,
    DiagramModuleSpec,
    DiagramNode,
    DiagramPortSide,
    DiagramRouteHint,
    DiagramRoutePoint,
    DiagramRoutingArtifact,
    DiagramRoutingSheet,
    DiagramContinuationMarker,
    PidLiteDiagramArtifact,
    DiagramSheet,
    DiagramSheetComposition,
    DiagramSheetCompositionArtifact,
    DiagramSymbolDefinition,
    DiagramSymbolLibraryArtifact,
    DiagramSymbolPolicy,
    DiagramSymbolShape,
    DiagramStyleProfile,
    DiagramTargetProfile,
    EnergyBalance,
    EquipmentListArtifact,
    FlowsheetBlueprintArtifact,
    FlowsheetCase,
    FlowsheetGraph,
    DiagramLinePattern,
    PlantDiagramConnection,
    PlantDiagramEntity,
    PlantDiagramSemanticsArtifact,
    ProcessFlowDiagramArtifact,
    ProjectBasis,
    StreamTable,
    utc_now,
)


def apply_diagram_drafting_metadata(
    sheets: list[DiagramSheet],
    *,
    drawing_prefix: str,
    prepared_by: str = "AoC",
    revision: str = "A",
    issue_status: str = "For Review",
) -> None:
    total = len(sheets)
    for index, sheet in enumerate(sheets, start=1):
        if not sheet.drawing_number:
            clean_prefix = re.sub(r"[^A-Za-z0-9_-]+", "-", drawing_prefix).strip("-").upper() or "AOC-DIAG"
            sheet.drawing_number = f"{clean_prefix}-{index:03d}"
        if not sheet.sheet_number:
            sheet.sheet_number = f"{index} of {total}"
        if not sheet.revision:
            sheet.revision = revision
        if not sheet.revision_date:
            sheet.revision_date = utc_now()[:10]
        if not sheet.issue_status:
            sheet.issue_status = issue_status
        if not sheet.prepared_by:
            sheet.prepared_by = prepared_by


def apply_diagram_review_workflow_metadata(
    sheets: list[DiagramSheet],
    *,
    checked_by: str = "",
    reviewed_by: str = "",
    approved_by: str = "",
    approved_date: str = "",
) -> None:
    for sheet in sheets:
        if checked_by and not sheet.checked_by:
            sheet.checked_by = checked_by
        if reviewed_by and not sheet.reviewed_by:
            sheet.reviewed_by = reviewed_by
        if approved_by and not sheet.approved_by:
            sheet.approved_by = approved_by
        if approved_date and not sheet.approved_date:
            sheet.approved_date = approved_date


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


def build_diagram_symbol_library() -> DiagramSymbolLibraryArtifact:
    symbols = [
        DiagramSymbolDefinition(
            symbol_key="bfd_process_block",
            label="Process Block",
            diagram_level=DiagramLevel.BFD,
            entity_kind=DiagramEntityKind.SECTION,
            shape=DiagramSymbolShape.ROUNDED_RECT,
            width_px=220,
            height_px=88,
            equipment_tag_position="hidden",
            notes=["The only allowed BFD block symbol."],
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_reactor",
            label="Reactor",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.VESSEL,
            width_px=160,
            height_px=82,
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_column",
            label="Distillation Column",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.COLUMN,
            width_px=110,
            height_px=210,
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_vessel",
            label="Vessel",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.VESSEL,
            width_px=138,
            height_px=88,
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_exchanger",
            label="Heat Exchanger",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.EXCHANGER,
            width_px=132,
            height_px=72,
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_pump",
            label="Pump",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.PUMP,
            width_px=110,
            height_px=64,
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_tank",
            label="Tank",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.VESSEL,
            width_px=138,
            height_px=84,
        ),
        DiagramSymbolDefinition(
            symbol_key="pfd_terminal",
            label="Terminal",
            diagram_level=DiagramLevel.PFD,
            entity_kind=DiagramEntityKind.STREAM_TERMINAL,
            shape=DiagramSymbolShape.TERMINAL,
            width_px=110,
            height_px=44,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="control_unit_ref",
            label="Controlled Unit Reference",
            diagram_level=DiagramLevel.CONTROL,
            entity_kind=DiagramEntityKind.UNIT,
            shape=DiagramSymbolShape.ROUNDED_RECT,
            width_px=170,
            height_px=64,
        ),
        DiagramSymbolDefinition(
            symbol_key="control_loop",
            label="Control Loop",
            diagram_level=DiagramLevel.CONTROL,
            entity_kind=DiagramEntityKind.CONTROL_LOOP,
            shape=DiagramSymbolShape.DIAMOND,
            width_px=120,
            height_px=76,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="control_instrument",
            label="Instrument Bubble",
            diagram_level=DiagramLevel.CONTROL,
            entity_kind=DiagramEntityKind.INSTRUMENT,
            shape=DiagramSymbolShape.INSTRUMENT_BUBBLE,
            width_px=56,
            height_px=56,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_unit",
            label="P&ID-lite Unit",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.UNIT,
            pid_family="equipment",
            shape=DiagramSymbolShape.ROUNDED_RECT,
            width_px=170,
            height_px=72,
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_indicator",
            label="P&ID-lite Indicator",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.INSTRUMENT,
            pid_family="indicator",
            shape=DiagramSymbolShape.INSTRUMENT_BUBBLE,
            width_px=54,
            height_px=54,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_transmitter",
            label="P&ID-lite Transmitter",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.INSTRUMENT,
            pid_family="transmitter",
            shape=DiagramSymbolShape.INSTRUMENT_BUBBLE,
            width_px=54,
            height_px=54,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_controller",
            label="P&ID-lite Controller",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.INSTRUMENT,
            pid_family="controller",
            shape=DiagramSymbolShape.DIAMOND,
            width_px=64,
            height_px=64,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_manual_valve",
            label="P&ID-lite Manual Valve",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.VALVE,
            pid_family="manual_valve",
            shape=DiagramSymbolShape.VALVE,
            width_px=48,
            height_px=48,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_control_valve",
            label="P&ID-lite Control Valve",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.VALVE,
            pid_family="control_valve",
            shape=DiagramSymbolShape.VALVE,
            width_px=52,
            height_px=52,
            equipment_tag_position="hidden",
        ),
        DiagramSymbolDefinition(
            symbol_key="pid_relief_valve",
            label="P&ID-lite Relief Valve",
            diagram_level=DiagramLevel.PID_LITE,
            entity_kind=DiagramEntityKind.VALVE,
            pid_family="relief_valve",
            shape=DiagramSymbolShape.VALVE,
            width_px=50,
            height_px=50,
            equipment_tag_position="hidden",
        ),
    ]
    edge_styles = [
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PROCESS, diagram_level=DiagramLevel.BFD, stroke_color="#111111"),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.RECYCLE, diagram_level=DiagramLevel.BFD, stroke_color="#5d6d7e", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PURGE, diagram_level=DiagramLevel.BFD, stroke_color="#6b7280", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.VENT, diagram_level=DiagramLevel.BFD, stroke_color="#6b7280", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.WASTE, diagram_level=DiagramLevel.BFD, stroke_color="#7f1d1d", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PROCESS, diagram_level=DiagramLevel.PFD, stroke_color="#111111"),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PRODUCT, diagram_level=DiagramLevel.PFD, stroke_color="#111111"),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.RECYCLE, diagram_level=DiagramLevel.PFD, stroke_color="#5d6d7e", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PURGE, diagram_level=DiagramLevel.PFD, stroke_color="#6b7280", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.VENT, diagram_level=DiagramLevel.PFD, stroke_color="#6b7280", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.WASTE, diagram_level=DiagramLevel.PFD, stroke_color="#7f1d1d", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.UTILITY, diagram_level=DiagramLevel.PFD, stroke_color="#4a6fa5", line_pattern=DiagramLinePattern.DOTTED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.CONTROL_SIGNAL, diagram_level=DiagramLevel.CONTROL, stroke_color="#8b1e3f", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.SAFEGUARD, diagram_level=DiagramLevel.CONTROL, stroke_color="#c2410c", line_pattern=DiagramLinePattern.DOTTED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.CONTINUATION, diagram_level=DiagramLevel.CONTROL, stroke_color="#475569", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.CONTROL_SIGNAL, diagram_level=DiagramLevel.PID_LITE, stroke_color="#8b1e3f", line_pattern=DiagramLinePattern.DASHED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PROCESS, diagram_level=DiagramLevel.PID_LITE, stroke_color="#111111"),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.PRODUCT, diagram_level=DiagramLevel.PID_LITE, stroke_color="#111111"),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.UTILITY, diagram_level=DiagramLevel.PID_LITE, stroke_color="#4a6fa5", line_pattern=DiagramLinePattern.DOTTED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.SAFEGUARD, diagram_level=DiagramLevel.PID_LITE, stroke_color="#c2410c", line_pattern=DiagramLinePattern.DOTTED),
        DiagramEdgeStyleRule(role=DiagramEdgeRole.CONTINUATION, diagram_level=DiagramLevel.PID_LITE, stroke_color="#475569", line_pattern=DiagramLinePattern.DASHED),
    ]
    level_policies = [
        DiagramLevelStylePolicy(
            diagram_level=DiagramLevel.BFD,
            symbol_policy=DiagramSymbolPolicy.BLOCK_ONLY,
            allowed_symbol_keys=["bfd_process_block"],
            forbidden_entity_kinds=[DiagramEntityKind.UNIT, DiagramEntityKind.CONTROL_LOOP, DiagramEntityKind.INSTRUMENT, DiagramEntityKind.VALVE],
            allowed_edge_roles=[DiagramEdgeRole.PROCESS, DiagramEdgeRole.RECYCLE, DiagramEdgeRole.PURGE, DiagramEdgeRole.VENT, DiagramEdgeRole.WASTE],
            primary_label_font_size_px=15,
            secondary_label_font_size_px=10,
            minimum_node_spacing_px=52,
            notes=["BFD stays section-level and may not show equipment or instrument detail."],
        ),
        DiagramLevelStylePolicy(
            diagram_level=DiagramLevel.PFD,
            symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
            allowed_symbol_keys=["pfd_reactor", "pfd_column", "pfd_vessel", "pfd_exchanger", "pfd_pump", "pfd_tank", "pfd_terminal"],
            forbidden_entity_kinds=[DiagramEntityKind.CONTROL_LOOP, DiagramEntityKind.INSTRUMENT, DiagramEntityKind.VALVE],
            allowed_edge_roles=[DiagramEdgeRole.PROCESS, DiagramEdgeRole.PRODUCT, DiagramEdgeRole.RECYCLE, DiagramEdgeRole.PURGE, DiagramEdgeRole.VENT, DiagramEdgeRole.WASTE, DiagramEdgeRole.UTILITY],
            primary_label_font_size_px=13,
            secondary_label_font_size_px=10,
            minimum_node_spacing_px=44,
            notes=["PFD uses equipment-level symbols only and excludes instrument bubble or valve clutter."],
        ),
        DiagramLevelStylePolicy(
            diagram_level=DiagramLevel.CONTROL,
            symbol_policy=DiagramSymbolPolicy.CONTROL_ONLY,
            allowed_symbol_keys=["control_unit_ref", "control_loop", "control_instrument"],
            forbidden_entity_kinds=[DiagramEntityKind.VALVE],
            allowed_edge_roles=[DiagramEdgeRole.CONTROL_SIGNAL, DiagramEdgeRole.SAFEGUARD, DiagramEdgeRole.CONTINUATION],
            primary_label_font_size_px=12,
            secondary_label_font_size_px=10,
            minimum_node_spacing_px=36,
            notes=["Control sheets show loop structure and safeguard logic, not process piping."],
        ),
        DiagramLevelStylePolicy(
            diagram_level=DiagramLevel.PID_LITE,
            symbol_policy=DiagramSymbolPolicy.PID_LITE_ONLY,
            allowed_symbol_keys=[
                "pid_unit",
                "pid_indicator",
                "pid_transmitter",
                "pid_controller",
                "pid_manual_valve",
                "pid_control_valve",
                "pid_relief_valve",
            ],
            forbidden_entity_kinds=[],
            allowed_edge_roles=[
                DiagramEdgeRole.PROCESS,
                DiagramEdgeRole.PRODUCT,
                DiagramEdgeRole.UTILITY,
                DiagramEdgeRole.CONTROL_SIGNAL,
                DiagramEdgeRole.SAFEGUARD,
                DiagramEdgeRole.CONTINUATION,
            ],
            primary_label_font_size_px=11,
            secondary_label_font_size_px=9,
            minimum_node_spacing_px=30,
            notes=[
                "P&ID-lite remains isolated per equipment cluster and must not replace the PFD.",
                "P&ID-lite may show valves, transmitters, indicators, controllers, and relief protection around a local unit cluster.",
            ],
        ),
    ]
    markdown = (
        "### Canonical Diagram Symbol Library\n\n"
        "- BFD uses one block symbol only\n"
        "- PFD uses equipment-level process symbols only\n"
        "- Control uses abstract unit references, loop diamonds, and instrument bubbles\n"
        "- P&ID-lite uses isolated valve, transmitter, indicator, controller, and relief symbols\n"
    )
    return DiagramSymbolLibraryArtifact(
        library_id="academic_process_symbol_library_v1",
        library_name="Academic Chemical Process Diagram Symbol Library",
        symbols=symbols,
        edge_styles=edge_styles,
        level_policies=level_policies,
        markdown=markdown,
    )


def build_diagram_equipment_templates() -> DiagramEquipmentTemplateArtifact:
    templates = [
        DiagramEquipmentTemplate(
            template_id="template_reactor",
            family="reactor",
            match_tokens=["reactor", "cstr", "pfr"],
            node_family="reactor",
            pfd_symbol_key="pfd_reactor",
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                DiagramEquipmentPortTemplate(port_role="measurement", side=DiagramPortSide.LEFT, lane="control", order_index=3),
                DiagramEquipmentPortTemplate(port_role="safeguard", side=DiagramPortSide.TOP, lane="safeguard", order_index=4),
            ],
        ),
        DiagramEquipmentTemplate(
            template_id="template_column",
            family="column",
            match_tokens=["column", "distillation"],
            node_family="column",
            pfd_symbol_key="pfd_column",
            default_width_px=150,
            default_height_px=180,
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                DiagramEquipmentPortTemplate(port_role="overhead", side=DiagramPortSide.TOP, lane="utility", order_index=3),
                DiagramEquipmentPortTemplate(port_role="bottoms", side=DiagramPortSide.BOTTOM, lane="product", order_index=4),
            ],
        ),
        DiagramEquipmentTemplate(
            template_id="template_vessel",
            family="vessel",
            match_tokens=["vessel", "separator", "flash", "drum"],
            node_family="vessel",
            pfd_symbol_key="pfd_vessel",
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                DiagramEquipmentPortTemplate(port_role="vent", side=DiagramPortSide.TOP, lane="vent", order_index=3),
                DiagramEquipmentPortTemplate(port_role="drain", side=DiagramPortSide.BOTTOM, lane="waste", order_index=4),
            ],
        ),
        DiagramEquipmentTemplate(
            template_id="template_heat_exchanger",
            family="heat_exchanger",
            match_tokens=["exchanger", "heater", "cooler", "condenser", "reboiler"],
            node_family="heat exchanger",
            pfd_symbol_key="pfd_exchanger",
            default_width_px=132,
            default_height_px=72,
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                DiagramEquipmentPortTemplate(port_role="utility_inlet", side=DiagramPortSide.TOP, lane="utility", order_index=3),
                DiagramEquipmentPortTemplate(port_role="utility_outlet", side=DiagramPortSide.BOTTOM, lane="utility", order_index=4),
            ],
        ),
        DiagramEquipmentTemplate(
            template_id="template_pump",
            family="pump",
            match_tokens=["pump", "compressor", "blower"],
            node_family="pump",
            pfd_symbol_key="pfd_pump",
            default_width_px=132,
            default_height_px=92,
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
            ],
        ),
        DiagramEquipmentTemplate(
            template_id="template_tank",
            family="tank",
            match_tokens=["tank", "storage"],
            node_family="tank",
            pfd_symbol_key="pfd_tank",
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                DiagramEquipmentPortTemplate(port_role="vent", side=DiagramPortSide.TOP, lane="vent", order_index=3),
            ],
        ),
        DiagramEquipmentTemplate(
            template_id="template_terminal",
            family="terminal",
            match_tokens=["terminal", "feed inlet", "outlet"],
            node_family="terminal",
            pfd_symbol_key="pfd_terminal",
            default_width_px=120,
            default_height_px=80,
            ports=[
                DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
            ],
        ),
    ]
    return DiagramEquipmentTemplateArtifact(
        artifact_id="diagram_equipment_templates_v1",
        templates=templates,
        markdown=(
            "### Equipment Templates\n\n"
            f"- Template families: {len(templates)}\n"
            "- Provides reusable family and port defaults for process and local instrumentation diagrams.\n"
        ),
        assumptions=["Equipment templates provide reusable symbol and port-side defaults before deeper per-domain specialization is introduced."],
    )


def build_diagram_domain_packs() -> DiagramDomainPackArtifact:
    packs = [
        DiagramDomainPack(
            pack_id="specialty_chemicals",
            label="Specialty Chemicals",
            match_tokens=["specialty", "fine chemical", "intermediate", "quat", "bac", "benzalkonium"],
            required_bfd_sections=[
                "feed preparation",
                "reaction",
                "cleanup",
                "concentration",
                "purification",
                "storage",
                "waste handling",
            ],
            required_pfd_unit_families=["reactor", "separator", "column", "vessel", "heat exchanger", "tank", "pump"],
            major_stream_roles=["feed", "product", "recycle", "purge", "vent", "waste", "side_draw"],
            preferred_template_families=["reactor", "vessel", "column", "heat_exchanger", "tank"],
            main_body_max_pfd_nodes=6,
            module_row_width_fraction=0.72,
            connector_mid_x_spacing_px=28,
            connector_lane_y_spacing_px=18,
            allowed_pfd_symbol_keys=["pfd_reactor", "pfd_column", "pfd_vessel", "pfd_exchanger", "pfd_pump", "pfd_tank", "pfd_terminal"],
            notes=["Default pack for batch-like and specialty-chemical process routes."],
        ),
        DiagramDomainPack(
            pack_id="petrochemicals",
            label="Petrochemicals",
            match_tokens=["ethylene", "propylene", "aromatic", "petrochemical", "refinery", "cracker"],
            required_bfd_sections=[
                "feed preparation",
                "reaction",
                "compression",
                "separation",
                "purification",
                "storage",
                "waste handling",
            ],
            required_pfd_unit_families=["reactor", "column", "separator", "heat exchanger", "pump", "tank"],
            major_stream_roles=["feed", "product", "recycle", "purge", "vent", "waste", "side_draw", "fuel_gas"],
            preferred_template_families=["column", "heat_exchanger", "pump", "vessel"],
            main_body_max_pfd_nodes=7,
            module_row_width_fraction=0.78,
            connector_mid_x_spacing_px=24,
            connector_lane_y_spacing_px=16,
            template_overrides={
                "column": DiagramEquipmentTemplate(
                    template_id="template_column_petrochemical",
                    family="column",
                    match_tokens=["column", "distillation", "fractionator"],
                    node_family="column",
                    pfd_symbol_key="pfd_column",
                    default_width_px=165,
                    default_height_px=220,
                    ports=[
                        DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                        DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                        DiagramEquipmentPortTemplate(port_role="overhead", side=DiagramPortSide.TOP, lane="product", order_index=3),
                        DiagramEquipmentPortTemplate(port_role="bottoms", side=DiagramPortSide.BOTTOM, lane="product", order_index=4),
                    ],
                    notes=["Petrochemical columns use larger continuous-service defaults."],
                ),
                "heat_exchanger": DiagramEquipmentTemplate(
                    template_id="template_heat_exchanger_petrochemical",
                    family="heat_exchanger",
                    match_tokens=["exchanger", "heater", "cooler", "condenser", "reboiler"],
                    node_family="heat exchanger",
                    pfd_symbol_key="pfd_exchanger",
                    default_width_px=150,
                    default_height_px=84,
                    ports=[
                        DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                        DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                        DiagramEquipmentPortTemplate(port_role="utility_inlet", side=DiagramPortSide.TOP, lane="utility", order_index=3),
                        DiagramEquipmentPortTemplate(port_role="utility_outlet", side=DiagramPortSide.BOTTOM, lane="utility", order_index=4),
                    ],
                    notes=["Petrochemical exchanger services use larger package geometry."],
                ),
            },
            allowed_pfd_symbol_keys=["pfd_reactor", "pfd_column", "pfd_vessel", "pfd_exchanger", "pfd_pump", "pfd_tank", "pfd_terminal"],
            notes=["Biases toward separation/compression-heavy continuous flows."],
        ),
        DiagramDomainPack(
            pack_id="utility_dense_process",
            label="Utility-Dense Process",
            match_tokens=["utility", "steam", "cooling water", "energy recovery", "utility-dense"],
            required_bfd_sections=[
                "feed preparation",
                "reaction",
                "heat recovery",
                "purification",
                "utilities",
                "storage",
                "waste handling",
            ],
            required_pfd_unit_families=["reactor", "heat exchanger", "vessel", "tank", "pump"],
            major_stream_roles=["feed", "product", "recycle", "vent", "waste", "utility", "condensate"],
            preferred_template_families=["heat_exchanger", "pump", "vessel"],
            main_body_max_pfd_nodes=5,
            module_row_width_fraction=0.64,
            connector_mid_x_spacing_px=34,
            connector_lane_y_spacing_px=22,
            template_overrides={
                "heat_exchanger": DiagramEquipmentTemplate(
                    template_id="template_heat_exchanger_utility_dense",
                    family="heat_exchanger",
                    match_tokens=["exchanger", "heater", "cooler", "condenser", "reboiler", "economizer"],
                    node_family="heat exchanger",
                    pfd_symbol_key="pfd_exchanger",
                    default_width_px=160,
                    default_height_px=96,
                    ports=[
                        DiagramEquipmentPortTemplate(port_role="process_inlet", side=DiagramPortSide.LEFT, order_index=1),
                        DiagramEquipmentPortTemplate(port_role="process_outlet", side=DiagramPortSide.RIGHT, order_index=2),
                        DiagramEquipmentPortTemplate(port_role="utility_inlet", side=DiagramPortSide.TOP, lane="utility", order_index=3),
                        DiagramEquipmentPortTemplate(port_role="utility_outlet", side=DiagramPortSide.BOTTOM, lane="utility", order_index=4),
                    ],
                    notes=["Utility-dense exchangers reserve larger utility attachment geometry."],
                ),
            },
            allowed_pfd_symbol_keys=["pfd_reactor", "pfd_vessel", "pfd_exchanger", "pfd_pump", "pfd_tank", "pfd_terminal"],
            notes=["Uses tighter per-sheet density limits to keep utility-heavy PFDs readable."],
        ),
    ]
    return DiagramDomainPackArtifact(
        artifact_id="diagram_domain_packs_v1",
        packs=packs,
        markdown=(
            "### Diagram Domain Packs\n\n"
            f"- Packs: {len(packs)}\n"
            "- Provides domain-specific defaults for sections, equipment-family expectations, stream roles, and density budgets.\n"
        ),
        assumptions=["Domain packs tune generic diagram architecture to common plant families before deeper domain-specialized renderers are introduced."],
    )


def _select_diagram_domain_pack(project_basis: ProjectBasis, domain_packs: DiagramDomainPackArtifact) -> DiagramDomainPack:
    lowered = project_basis.target_product.lower()
    for pack in domain_packs.packs:
        if any(token in lowered for token in pack.match_tokens):
            return pack
    return next(pack for pack in domain_packs.packs if pack.pack_id == "specialty_chemicals")


def _domain_pack_by_id(pack_id: str, domain_packs: DiagramDomainPackArtifact | None = None) -> DiagramDomainPack | None:
    packs = domain_packs or build_diagram_domain_packs()
    return next((pack for pack in packs.packs if pack.pack_id == pack_id), None)


def build_domain_equipment_templates(domain_pack_id: str) -> DiagramEquipmentTemplateArtifact:
    base = build_diagram_equipment_templates()
    selected_pack = _domain_pack_by_id(domain_pack_id)
    if selected_pack is None or not selected_pack.template_overrides:
        return base
    templates: list[DiagramEquipmentTemplate] = []
    for template in base.templates:
        override = selected_pack.template_overrides.get(template.family)
        templates.append(override.model_copy(deep=True) if override is not None else template.model_copy(deep=True))
    known_families = {template.family for template in templates}
    for family, override in selected_pack.template_overrides.items():
        if family not in known_families:
            templates.append(override.model_copy(deep=True))
    return DiagramEquipmentTemplateArtifact(
        artifact_id=f"{base.artifact_id}_{selected_pack.pack_id}",
        templates=templates,
        markdown=(
            "### Domain Equipment Templates\n\n"
            f"- Domain pack: {selected_pack.label}\n"
            f"- Override families: {', '.join(sorted(selected_pack.template_overrides)) or 'none'}\n"
        ),
        assumptions=base.assumptions + [f"Applied template overrides for domain pack `{selected_pack.pack_id}`."],
    )


def _equipment_template_for_text(
    unit_type: str,
    label: str,
    templates: DiagramEquipmentTemplateArtifact,
    preferred_families: list[str] | None = None,
) -> DiagramEquipmentTemplate:
    lowered = f"{unit_type} {label}".lower()
    matches = [template for template in templates.templates if any(token in lowered for token in template.match_tokens)]
    if matches:
        preferred_order = {family: index for index, family in enumerate(preferred_families or [])}
        matches.sort(key=lambda template: (preferred_order.get(template.family, len(preferred_order)), templates.templates.index(template)))
        return matches[0]
    return next(template for template in templates.templates if template.family == "vessel")


def _template_port_side_for_connection(
    entity: PlantDiagramEntity | None,
    connection: PlantDiagramConnection,
    direction: str,
    templates: DiagramEquipmentTemplateArtifact,
) -> DiagramPortSide:
    unit_type = entity.metadata.get("unit_type", "") if entity is not None else ""
    label = entity.label if entity is not None else ""
    template = _equipment_template_for_text(unit_type, label, templates)
    if connection.role == DiagramEdgeRole.PROCESS:
        port_role = "process_outlet" if direction == "out" else "process_inlet"
    elif connection.role == DiagramEdgeRole.RECYCLE:
        port_role = "process_outlet" if direction == "out" else "process_inlet"
    elif connection.role == DiagramEdgeRole.VENT:
        port_role = "vent" if direction == "out" else "process_inlet"
    elif connection.role == DiagramEdgeRole.WASTE:
        port_role = "drain" if direction == "out" else "process_inlet"
    else:
        port_role = "process_outlet" if direction == "out" else "process_inlet"
    port = next((item for item in template.ports if item.port_role == port_role), None)
    if port is not None:
        return port.side
    return DiagramPortSide.RIGHT if direction == "out" else DiagramPortSide.LEFT


def _template_family_to_node_family(family: str) -> str:
    normalized = family.strip().lower()
    if normalized == "heat_exchanger":
        return "heat exchanger"
    if normalized in {"reactor", "column", "vessel", "pump", "tank", "terminal"}:
        return normalized
    return "vessel"


def _template_for_family(
    family: str,
    templates: DiagramEquipmentTemplateArtifact,
) -> DiagramEquipmentTemplate | None:
    normalized = family.strip().lower()
    return next((template for template in templates.templates if template.family == normalized), None)


def _connection_template_port_role(
    entity: PlantDiagramEntity | None,
    connection: PlantDiagramConnection,
    direction: str,
    templates: DiagramEquipmentTemplateArtifact,
    context_text: str = "",
) -> str:
    if entity is None:
        return "process_outlet" if direction == "out" else "process_inlet"
    template_family = entity.metadata.get("template_family", "")
    template = _template_for_family(template_family, templates)
    if template is None:
        unit_type = entity.metadata.get("unit_type", "")
        template = _equipment_template_for_text(unit_type, entity.label, templates)
    available_roles = {port.port_role for port in template.ports}
    text = " ".join(
        part
        for part in [
            connection.label,
            connection.stream_id,
            connection.condition_label,
            connection.preferred_lane,
            context_text,
        ]
        if part
    ).lower()
    if connection.role == DiagramEdgeRole.UTILITY:
        role = "utility_outlet" if direction == "out" else "utility_inlet"
        if role in available_roles:
            return role
    if direction == "out":
        if "overhead" in text and "overhead" in available_roles:
            return "overhead"
        if any(token in text for token in {"bottom", "bottoms", "residue"}) and "bottoms" in available_roles:
            return "bottoms"
        if connection.role == DiagramEdgeRole.VENT and "vent" in available_roles:
            return "vent"
        if connection.role == DiagramEdgeRole.WASTE and "drain" in available_roles:
            return "drain"
        if connection.role == DiagramEdgeRole.SAFEGUARD and "safeguard" in available_roles:
            return "safeguard"
        if connection.role == DiagramEdgeRole.CONTROL_SIGNAL and "measurement" in available_roles:
            return "measurement"
        if "process_outlet" in available_roles:
            return "process_outlet"
    else:
        if "overhead" in text and "overhead" in available_roles:
            return "overhead"
        if any(token in text for token in {"bottom", "bottoms", "residue"}) and "bottoms" in available_roles:
            return "bottoms"
        if connection.role == DiagramEdgeRole.UTILITY:
            if "utility_inlet" in available_roles:
                return "utility_inlet"
        if "process_inlet" in available_roles:
            return "process_inlet"
    return "process_outlet" if direction == "out" else "process_inlet"


def build_diagram_target_profile(project_basis: ProjectBasis) -> DiagramTargetProfile:
    product_key = re.sub(r"[^a-z0-9]+", "_", project_basis.target_product.lower()).strip("_") or "project"
    domain_packs = build_diagram_domain_packs()
    selected_pack = _select_diagram_domain_pack(project_basis, domain_packs)
    return DiagramTargetProfile(
        target_id=f"{product_key}_diagram_target_v1",
        target_product=project_basis.target_product,
        domain_pack_id=selected_pack.pack_id,
        required_bfd_sections=selected_pack.required_bfd_sections,
        required_pfd_unit_families=selected_pack.required_pfd_unit_families,
        major_stream_roles=selected_pack.major_stream_roles,
        preferred_template_families=selected_pack.preferred_template_families,
        allowed_pfd_symbol_keys=selected_pack.allowed_pfd_symbol_keys,
        main_body_max_pfd_nodes=selected_pack.main_body_max_pfd_nodes,
        module_row_width_fraction=selected_pack.module_row_width_fraction,
        connector_mid_x_spacing_px=selected_pack.connector_mid_x_spacing_px,
        connector_lane_y_spacing_px=selected_pack.connector_lane_y_spacing_px,
        markdown=(
            "### Diagram Target Profile\n\n"
            f"- Domain pack: {selected_pack.label}\n"
            "- BFD stays section-level\n"
            "- PFD stays report-grade equipment-level rather than full P&ID detail\n"
        ),
        assumptions=[f"Diagram target profile selected the `{selected_pack.pack_id}` domain pack based on target-product heuristics."],
    )


def build_block_flow_diagram_semantics(
    blueprint: FlowsheetBlueprintArtifact,
    target: DiagramTargetProfile,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> PlantDiagramSemanticsArtifact:
    level_policy = next(policy for policy in symbol_library.level_policies if policy.diagram_level == DiagramLevel.BFD)
    allowed_symbol_key = level_policy.allowed_symbol_keys[0] if level_policy.allowed_symbol_keys else "bfd_process_block"
    entities: list[PlantDiagramEntity] = []
    connections: list[PlantDiagramConnection] = []
    section_to_entity_id: dict[str, str] = {}
    section_order: list[str] = []
    step_to_section_entity_id: dict[str, str] = {}

    def register_section(section_key: str, display_label: str) -> str:
        if section_key in section_to_entity_id:
            return section_to_entity_id[section_key]
        entity_id = f"bfd_section_{re.sub(r'[^a-z0-9]+', '_', section_key.lower()).strip('_') or 'section'}"
        section_to_entity_id[section_key] = entity_id
        section_order.append(section_key)
        entities.append(
            PlantDiagramEntity(
                entity_id=entity_id,
                kind=DiagramEntityKind.SECTION,
                label=display_label,
                diagram_level=DiagramLevel.BFD,
                section_id=section_key,
                symbol_key=allowed_symbol_key,
                preferred_module_id=f"bfd_module_{re.sub(r'[^a-z0-9]+', '_', section_key.lower()).strip('_') or 'section'}",
                metadata={"display_label": display_label},
            )
        )
        return entity_id

    previous_section_key = ""
    seen_transition_pairs: set[tuple[str, str]] = set()
    edge_counter = 1
    for step in blueprint.steps:
        section_key = _canonical_bfd_section(step.section_label or step.section_id or step.service)
        display_label = _display_bfd_section(section_key)
        entity_id = register_section(section_key, display_label)
        step_to_section_entity_id[step.step_id] = entity_id
        if previous_section_key and previous_section_key != section_key:
            pair = (previous_section_key, section_key)
            if pair not in seen_transition_pairs:
                connections.append(
                    PlantDiagramConnection(
                        connection_id=f"bfd_conn_{edge_counter}",
                        role=DiagramEdgeRole.PROCESS,
                        diagram_level=DiagramLevel.BFD,
                        source_entity_id=section_to_entity_id[previous_section_key],
                        target_entity_id=section_to_entity_id[section_key],
                        label="Main process flow",
                        must_route_externally=True,
                    )
                )
                edge_counter += 1
                seen_transition_pairs.add(pair)
        previous_section_key = section_key

    if _is_bac_target(target):
        for required in target.required_bfd_sections:
            if required not in section_to_entity_id:
                register_section(required, _display_bfd_section(required, target=target))
        section_order = _ordered_bfd_sections(section_to_entity_id.keys(), target)
        process_connections = []
        edge_counter = 1
        for left_key, right_key in zip(section_order, section_order[1:]):
            process_connections.append(
                PlantDiagramConnection(
                    connection_id=f"bfd_conn_{edge_counter}",
                    role=DiagramEdgeRole.PROCESS,
                    diagram_level=DiagramLevel.BFD,
                    source_entity_id=section_to_entity_id[left_key],
                    target_entity_id=section_to_entity_id[right_key],
                    label="Main process flow",
                    must_route_externally=True,
                )
            )
            edge_counter += 1
        recycle_connections = [connection for connection in connections if connection.role == DiagramEdgeRole.RECYCLE]
        connections = process_connections + recycle_connections

    seen_recycles: set[tuple[str, str, str]] = set()
    for recycle in blueprint.recycle_intents:
        source_entity_id = step_to_section_entity_id.get(recycle.source_step_id)
        target_entity_id = step_to_section_entity_id.get(recycle.target_step_id)
        if not source_entity_id or not target_entity_id:
            continue
        recycle_key = (source_entity_id, target_entity_id, recycle.stream_family)
        if recycle_key in seen_recycles:
            continue
        label = "Recycle"
        if recycle.stream_family:
            label = f"Recycle ({recycle.stream_family.replace('_', ' ')})"
        connections.append(
            PlantDiagramConnection(
                connection_id=f"bfd_conn_{edge_counter}",
                role=DiagramEdgeRole.RECYCLE,
                diagram_level=DiagramLevel.BFD,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                label=label,
                must_route_externally=True,
                preferred_lane="recycle",
            )
        )
        edge_counter += 1
        seen_recycles.add(recycle_key)

    markdown = (
        "### BFD Semantics\n\n"
        f"- Sections: {len(entities)}\n"
        f"- Inter-section connections: {len(connections)}\n"
    )
    return PlantDiagramSemanticsArtifact(
        diagram_id=f"{blueprint.route_id}_bfd_semantics",
        route_id=blueprint.route_id,
        entities=entities,
        connections=connections,
        section_order=section_order,
        citations=blueprint.citations,
        assumptions=blueprint.assumptions + ["BFD semantics isolate process sections before module composition."],
        markdown=markdown,
    )


def build_block_flow_diagram_modules(
    semantics: PlantDiagramSemanticsArtifact,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> DiagramModuleArtifact:
    level_policy = next(policy for policy in symbol_library.level_policies if policy.diagram_level == DiagramLevel.BFD)
    connection_map = {connection.connection_id: connection for connection in semantics.connections}
    modules: list[DiagramModuleSpec] = []
    for entity in semantics.entities:
        module_id = entity.preferred_module_id or f"bfd_module_{entity.entity_id}"
        touching_connections = [
            connection
            for connection in semantics.connections
            if connection.source_entity_id == entity.entity_id or connection.target_entity_id == entity.entity_id
        ]
        boundary_ports: list[DiagramModulePort] = []
        for order_index, connection in enumerate(touching_connections, start=1):
            is_source = connection.source_entity_id == entity.entity_id
            side = DiagramPortSide.RIGHT if is_source and connection.role == DiagramEdgeRole.PROCESS else DiagramPortSide.LEFT
            if connection.role == DiagramEdgeRole.RECYCLE:
                side = DiagramPortSide.TOP if is_source else DiagramPortSide.BOTTOM
            boundary_ports.append(
                DiagramModulePort(
                    port_id=f"{module_id}__{connection.connection_id}__{'out' if is_source else 'in'}",
                    entity_id=entity.entity_id,
                    connection_role=connection.role,
                    side=side,
                    order_index=order_index,
                    lane=connection.preferred_lane,
                    label=connection.label,
                )
            )
        modules.append(
            DiagramModuleSpec(
                module_id=module_id,
                module_kind=DiagramLevel.BFD,
                title=entity.label,
                symbol_policy=level_policy.symbol_policy,
                section_id=entity.section_id,
                unit_ids=[],
                entity_ids=[entity.entity_id],
                connection_ids=[connection.connection_id for connection in touching_connections],
                boundary_ports=boundary_ports,
                allowed_edge_roles=level_policy.allowed_edge_roles,
                forbidden_entity_kinds=level_policy.forbidden_entity_kinds,
                preferred_orientation="LR",
                sheet_break_allowed=False,
                must_be_isolated=False,
                constraints=[
                    DiagramModuleConstraint(key="min_node_spacing_px", value=str(level_policy.minimum_node_spacing_px)),
                    DiagramModuleConstraint(key="min_label_clearance_px", value=str(level_policy.minimum_label_clearance_px)),
                    DiagramModuleConstraint(key="orthogonal_only", value="true"),
                ],
                notes=[f"Section module for {entity.label}."],
            )
        )
    markdown = (
        "### BFD Modules\n\n"
        f"- Section modules: {len(modules)}\n"
        "- Each module contains one section block and only boundary ports for inter-section stitching.\n"
    )
    return DiagramModuleArtifact(
        diagram_id=semantics.diagram_id.replace("_semantics", "_modules"),
        route_id=semantics.route_id,
        module_kind=DiagramLevel.BFD,
        modules=modules,
        citations=semantics.citations,
        assumptions=semantics.assumptions + ["BFD modules are isolated one-section slices for deterministic stitching."],
        markdown=markdown,
    )


def build_block_flow_diagram_sheet_composition(
    modules: DiagramModuleArtifact,
    semantics: PlantDiagramSemanticsArtifact,
    style: DiagramStyleProfile,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> DiagramSheetCompositionArtifact:
    symbol_map = {symbol.symbol_key: symbol for symbol in symbol_library.symbols}
    entity_map = {entity.entity_id: entity for entity in semantics.entities}
    module_by_entity: dict[str, DiagramModuleSpec] = {}
    for module in modules.modules:
        for entity_id in module.entity_ids:
            module_by_entity[entity_id] = module

    placements: list[DiagramModulePlacement] = []
    x_cursor = 90.0
    y_base = 220.0
    x_gap = 52.0
    for z_index, section_key in enumerate(semantics.section_order, start=1):
        entity = next((item for item in semantics.entities if item.section_id == section_key), None)
        if entity is None:
            continue
        module = module_by_entity.get(entity.entity_id)
        if module is None:
            continue
        symbol = symbol_map.get(entity.symbol_key or "bfd_process_block")
        width = float(symbol.width_px + 28 if symbol else 248)
        height = float(symbol.height_px + 22 if symbol else 110)
        placements.append(
            DiagramModulePlacement(
                module_id=module.module_id,
                sheet_id="sheet_1",
                x=x_cursor,
                y=y_base,
                width=width,
                height=height,
                z_index=z_index,
            )
        )
        x_cursor += width + x_gap

    connectors = []
    for connection in semantics.connections:
        source_module = module_by_entity.get(connection.source_entity_id)
        target_module = module_by_entity.get(connection.target_entity_id)
        if source_module is None or target_module is None:
            continue
        connectors.append(
            DiagramInterModuleConnector(
                connector_id=f"sheet_connector_{connection.connection_id}",
                role=connection.role,
                source_module_id=source_module.module_id,
                source_port_id=f"{source_module.module_id}__{connection.connection_id}__out",
                target_module_id=target_module.module_id,
                target_port_id=f"{target_module.module_id}__{connection.connection_id}__in",
                label=connection.label,
                continuation_marker="",
            )
        )
    width_px = max(style.canvas_width_px, int((max((placement.x + placement.width) for placement in placements) if placements else 0) + 120))
    height_px = max(style.canvas_height_px, 820)
    sheet = DiagramSheetComposition(
        sheet_id="sheet_1",
        title="Block Flow Diagram",
        diagram_level=DiagramLevel.BFD,
        width_px=width_px,
        height_px=height_px,
        module_placements=placements,
        connectors=connectors,
        legend_mode="suppressed",
        title_block_mode="embedded",
    )
    markdown = (
        "### BFD Sheet Composition\n\n"
        f"- Placements: {len(placements)}\n"
        f"- Inter-module connectors: {len(connectors)}\n"
    )
    return DiagramSheetCompositionArtifact(
        diagram_id=modules.diagram_id.replace("_modules", "_sheet_composition"),
        route_id=modules.route_id,
        diagram_level=DiagramLevel.BFD,
        sheets=[sheet],
        citations=modules.citations,
        assumptions=modules.assumptions + ["BFD sheet composition places section modules left-to-right before SVG rendering."],
        markdown=markdown,
    )


def build_process_flow_diagram_semantics(
    flowsheet_graph: FlowsheetGraph,
    flowsheet_case: FlowsheetCase,
    stream_table: StreamTable,
    target: DiagramTargetProfile,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> PlantDiagramSemanticsArtifact:
    allowed_symbol_keys = {symbol.symbol_key: symbol for symbol in symbol_library.symbols if symbol.diagram_level == DiagramLevel.PFD}
    if target.allowed_pfd_symbol_keys:
        allowed_symbol_keys = {key: symbol for key, symbol in allowed_symbol_keys.items() if key in set(target.allowed_pfd_symbol_keys)}
    equipment_templates = build_domain_equipment_templates(target.domain_pack_id)

    entities: list[PlantDiagramEntity] = []
    connections: list[PlantDiagramConnection] = []
    section_order: list[str] = []
    node_ids = {node.node_id for node in flowsheet_graph.nodes}
    for section_id in flowsheet_graph.section_ids:
        if section_id and section_id not in section_order:
            section_order.append(section_id)
    for node in flowsheet_graph.nodes:
        if node.section_id and node.section_id not in section_order:
            section_order.append(node.section_id)
        template = _equipment_template_for_text(
            node.unit_type,
            node.label,
            equipment_templates,
            target.preferred_template_families,
        )
        symbol_key = template.pfd_symbol_key
        if symbol_key not in allowed_symbol_keys:
            symbol_key = "pfd_vessel"
        entities.append(
            PlantDiagramEntity(
                entity_id=node.node_id,
                kind=DiagramEntityKind.UNIT,
                label=node.label,
                diagram_level=DiagramLevel.PFD,
                section_id=node.section_id,
                unit_id=node.node_id,
                service=node.label,
                symbol_key=symbol_key,
                preferred_module_id=f"pfd_module_{re.sub(r'[^a-z0-9]+', '_', (node.section_id or 'misc').lower()).strip('_') or 'misc'}",
                metadata={
                    "unit_type": node.unit_type,
                    "section_type": node.section_type,
                    "template_id": template.template_id,
                    "template_family": template.family,
                    "domain_pack_id": target.domain_pack_id,
                },
            )
        )

    terminal_counter = 1
    source_override_by_stream: dict[str, str] = {}
    destination_override_by_stream: dict[str, str] = {}
    existing_entity_ids = {entity.entity_id for entity in entities}
    for stream in stream_table.streams:
        if stream.stream_role not in set(target.major_stream_roles):
            continue
        if stream.destination_unit_id is None and stream.source_unit_id:
            terminal_id = f"pfd_terminal_{stream.stream_role}_{terminal_counter}"
            if terminal_id not in existing_entity_ids:
                entities.append(
                    PlantDiagramEntity(
                        entity_id=terminal_id,
                        kind=DiagramEntityKind.STREAM_TERMINAL,
                        label=f"{stream.stream_role.title()} Outlet",
                        diagram_level=DiagramLevel.PFD,
                        section_id=stream.section_id,
                        stream_id=stream.stream_id,
                        symbol_key="pfd_terminal",
                        preferred_module_id=f"pfd_module_{re.sub(r'[^a-z0-9]+', '_', (stream.section_id or 'terminals').lower()).strip('_') or 'terminals'}",
                    )
                )
                existing_entity_ids.add(terminal_id)
                terminal_counter += 1
            destination_override_by_stream[stream.stream_id] = terminal_id
        elif stream.source_unit_id is None and stream.destination_unit_id:
            terminal_id = f"pfd_terminal_feed_{terminal_counter}"
            if terminal_id not in existing_entity_ids:
                entities.append(
                    PlantDiagramEntity(
                        entity_id=terminal_id,
                        kind=DiagramEntityKind.STREAM_TERMINAL,
                        label="Feed Inlet",
                        diagram_level=DiagramLevel.PFD,
                        section_id=stream.section_id,
                        stream_id=stream.stream_id,
                        symbol_key="pfd_terminal",
                        preferred_module_id=f"pfd_module_{re.sub(r'[^a-z0-9]+', '_', (stream.section_id or 'feed').lower()).strip('_') or 'feed'}",
                    )
                )
                existing_entity_ids.add(terminal_id)
                terminal_counter += 1
            source_override_by_stream[stream.stream_id] = terminal_id

    edge_counter = 1
    for stream in stream_table.streams:
        source_id = source_override_by_stream.get(stream.stream_id, stream.source_unit_id or "")
        target_id = destination_override_by_stream.get(stream.stream_id, stream.destination_unit_id or "")
        if not source_id or not target_id:
            continue
        if source_id not in existing_entity_ids or target_id not in existing_entity_ids:
            continue
        role = {
            "product": DiagramEdgeRole.PRODUCT,
            "recycle": DiagramEdgeRole.RECYCLE,
            "purge": DiagramEdgeRole.PURGE,
            "vent": DiagramEdgeRole.VENT,
            "waste": DiagramEdgeRole.WASTE,
        }.get(stream.stream_role, DiagramEdgeRole.PROCESS)
        label = _pfd_stream_label(stream.stream_id, stream.description, stream.stream_role)
        condition_label = ""
        if stream.temperature_c and stream.pressure_bar and role == DiagramEdgeRole.PROCESS:
            condition_label = f"{stream.temperature_c:.0f} C / {stream.pressure_bar:.1f} bar"
        connections.append(
            PlantDiagramConnection(
                connection_id=f"pfd_conn_{edge_counter}",
                role=role,
                diagram_level=DiagramLevel.PFD,
                source_entity_id=source_id,
                target_entity_id=target_id,
                stream_id=stream.stream_id,
                label=label,
                condition_label=condition_label,
                must_route_externally=(source_id not in node_ids or target_id not in node_ids),
                preferred_lane="main" if role == DiagramEdgeRole.PROCESS else role.value,
            )
        )
        edge_counter += 1

    for loop in flowsheet_case.recycle_loops:
        if not loop.recycle_source_unit_id or not loop.recycle_target_unit_id:
            continue
        if loop.recycle_source_unit_id not in existing_entity_ids or loop.recycle_target_unit_id not in existing_entity_ids:
            continue
        if any(
            connection.role == DiagramEdgeRole.RECYCLE
            and connection.source_entity_id == loop.recycle_source_unit_id
            and connection.target_entity_id == loop.recycle_target_unit_id
            for connection in connections
        ):
            continue
        connections.append(
            PlantDiagramConnection(
                connection_id=f"pfd_conn_{edge_counter}",
                role=DiagramEdgeRole.RECYCLE,
                diagram_level=DiagramLevel.PFD,
                source_entity_id=loop.recycle_source_unit_id,
                target_entity_id=loop.recycle_target_unit_id,
                label="Recycle loop",
                must_route_externally=True,
                preferred_lane="recycle",
            )
        )
        edge_counter += 1

    markdown = (
        "### PFD Semantics\n\n"
        f"- Unit and terminal entities: {len(entities)}\n"
        f"- Stream/recycle connections: {len(connections)}\n"
    )
    return PlantDiagramSemanticsArtifact(
        diagram_id=f"{flowsheet_graph.route_id}_pfd_semantics",
        route_id=flowsheet_graph.route_id,
        entities=entities,
        connections=connections,
        section_order=section_order,
        citations=sorted(set(flowsheet_graph.citations + flowsheet_case.citations + stream_table.citations)),
        assumptions=flowsheet_graph.assumptions + flowsheet_case.assumptions + stream_table.assumptions + ["PFD semantics isolate process equipment and terminal nodes before layout."],
        markdown=markdown,
    )


def build_process_flow_diagram_modules(
    semantics: PlantDiagramSemanticsArtifact,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> DiagramModuleArtifact:
    level_policy = next(policy for policy in symbol_library.level_policies if policy.diagram_level == DiagramLevel.PFD)
    domain_pack_id = next((entity.metadata.get("domain_pack_id", "") for entity in semantics.entities if entity.metadata.get("domain_pack_id")), "")
    equipment_templates = build_domain_equipment_templates(domain_pack_id)
    modules: list[DiagramModuleSpec] = []
    sections = list(semantics.section_order)
    for entity in semantics.entities:
        if entity.section_id and entity.section_id not in sections:
            sections.append(entity.section_id)
    for section_id in sections:
        section_entities = [entity for entity in semantics.entities if entity.section_id == section_id]
        if not section_entities:
            continue
        entity_ids = {entity.entity_id for entity in section_entities}
        touching_connections = [
            connection
            for connection in semantics.connections
            if connection.source_entity_id in entity_ids or connection.target_entity_id in entity_ids
        ]
        boundary_ports: list[DiagramModulePort] = []
        seen_ports: set[str] = set()
        for connection in touching_connections:
            for direction, entity_id in (("out", connection.source_entity_id), ("in", connection.target_entity_id)):
                if entity_id not in entity_ids:
                    continue
                port_id = f"pfd_module_{re.sub(r'[^a-z0-9]+', '_', section_id.lower()).strip('_') or 'misc'}__{connection.connection_id}__{direction}"
                if port_id in seen_ports:
                    continue
                is_external = {connection.source_entity_id, connection.target_entity_id} - entity_ids
                entity = next((item for item in section_entities if item.entity_id == entity_id), None)
                side = _template_port_side_for_connection(entity, connection, direction, equipment_templates)
                boundary_ports.append(
                    DiagramModulePort(
                        port_id=port_id,
                        entity_id=entity_id,
                        connection_role=connection.role,
                        template_port_role=_connection_template_port_role(entity, connection, direction, equipment_templates),
                        side=side,
                        order_index=len(boundary_ports) + 1,
                        lane=connection.preferred_lane,
                        label=connection.label if is_external else "",
                    )
                )
                seen_ports.add(port_id)
        modules.append(
            DiagramModuleSpec(
                module_id=f"pfd_module_{re.sub(r'[^a-z0-9]+', '_', section_id.lower()).strip('_') or 'misc'}",
                module_kind=DiagramLevel.PFD,
                title=_display_bfd_section(section_id),
                symbol_policy=level_policy.symbol_policy,
                section_id=section_id,
                unit_ids=[entity.unit_id for entity in section_entities if entity.unit_id],
                entity_ids=[entity.entity_id for entity in section_entities],
                connection_ids=[connection.connection_id for connection in touching_connections],
                boundary_ports=boundary_ports,
                allowed_edge_roles=level_policy.allowed_edge_roles,
                forbidden_entity_kinds=level_policy.forbidden_entity_kinds,
                preferred_orientation="LR",
                sheet_break_allowed=True,
                must_be_isolated=False,
                constraints=[
                    DiagramModuleConstraint(key="min_node_spacing_px", value=str(level_policy.minimum_node_spacing_px)),
                    DiagramModuleConstraint(key="min_label_clearance_px", value=str(level_policy.minimum_label_clearance_px)),
                    DiagramModuleConstraint(key="max_nodes", value="6"),
                    DiagramModuleConstraint(key="orthogonal_only", value="true"),
                ],
                notes=[f"PFD section module for {section_id}."],
            )
        )
    markdown = (
        "### PFD Modules\n\n"
        f"- Section modules: {len(modules)}\n"
        "- Each module groups process equipment by section before multi-sheet composition.\n"
    )
    return DiagramModuleArtifact(
        diagram_id=semantics.diagram_id.replace("_semantics", "_modules"),
        route_id=semantics.route_id,
        module_kind=DiagramLevel.PFD,
        modules=modules,
        citations=semantics.citations,
        assumptions=semantics.assumptions + ["PFD modules group process equipment by section for deterministic sheet splitting."],
        markdown=markdown,
    )


def build_process_flow_diagram_sheet_composition(
    modules: DiagramModuleArtifact,
    semantics: PlantDiagramSemanticsArtifact,
    style: DiagramStyleProfile,
    target: DiagramTargetProfile,
) -> DiagramSheetCompositionArtifact:
    module_map = {module.module_id: module for module in modules.modules}
    module_order = [module.module_id for module in modules.modules]
    module_sizes = {module_id: _estimate_pfd_module_footprint(module_map[module_id], semantics) for module_id in module_order}
    bac_pfd_mode = _is_bac_target(target)
    if bac_pfd_mode:
        return _build_bac_pfd_sheet_composition(modules, style)
    modules_per_sheet = max(1, target.main_body_max_pfd_nodes)
    sheet_width_budget = max(style.canvas_width_px, 1760 if bac_pfd_mode else 1500)
    sheet_height_budget = max(style.canvas_height_px, 1080 if bac_pfd_mode else 980)
    row_width_budget = max(1260.0 if bac_pfd_mode else 1200.0, sheet_width_budget * target.module_row_width_fraction)
    horizontal_gap = 72.0 if bac_pfd_mode else 70.0
    row_gap = 82.0 if bac_pfd_mode else 90.0
    sheets: list[DiagramSheetComposition] = []
    module_to_sheet: dict[str, str] = {}
    chunks = _plan_pfd_sheet_module_chunks(
        module_order,
        module_sizes,
        modules_per_sheet=modules_per_sheet,
        row_width_budget=row_width_budget,
        sheet_height_budget=sheet_height_budget,
        horizontal_gap=horizontal_gap,
        row_gap=row_gap,
    )
    for sheet_index, chunk in enumerate(chunks, start=1):
        placements: list[DiagramModulePlacement] = []
        row_layouts = _pack_pfd_modules_for_sheet(
            chunk,
            module_sizes,
            row_width_budget=row_width_budget,
            horizontal_gap=horizontal_gap,
        )
        y_cursor = 156.0 if bac_pfd_mode else 160.0
        z_index = 1
        for row in row_layouts:
            x_cursor = 88.0 if bac_pfd_mode else 80.0
            row_height = max((module_sizes[module_id][1] for module_id in row), default=0.0)
            for module_id in row:
                width, height = module_sizes[module_id]
                placements.append(
                    DiagramModulePlacement(
                        module_id=module_id,
                        sheet_id=f"sheet_{sheet_index}",
                        x=x_cursor,
                        y=y_cursor,
                        width=width,
                        height=height,
                        z_index=z_index,
                    )
                )
                z_index += 1
                module_to_sheet[module_id] = f"sheet_{sheet_index}"
                x_cursor += width + horizontal_gap
            y_cursor += row_height + row_gap
        max_sheet_width = max((placement.x + placement.width for placement in placements), default=0.0)
        max_sheet_height = max((placement.y + placement.height for placement in placements), default=0.0)
        width_padding = 180 if bac_pfd_mode else 140
        height_padding = 180 if bac_pfd_mode else 160
        density_driven_width = max(style.canvas_width_px, int(max_sheet_width + width_padding))
        density_driven_height = max(style.canvas_height_px, int(max_sheet_height + height_padding))
        density_driven_width = max(density_driven_width, min(int(sheet_width_budget * (1.08 if bac_pfd_mode else 1.15)), int(max_sheet_width + (220 if bac_pfd_mode else 180))))
        density_driven_height = max(density_driven_height, min(int(sheet_height_budget * (1.07 if bac_pfd_mode else 1.1)), int(max_sheet_height + (200 if bac_pfd_mode else 180))))
        sheets.append(
            DiagramSheetComposition(
                sheet_id=f"sheet_{sheet_index}",
                title="Process Flow Diagram" if sheet_index == 1 else f"PFD Sheet {sheet_index}",
                diagram_level=DiagramLevel.PFD,
                width_px=density_driven_width,
                height_px=density_driven_height,
                module_placements=placements,
                connectors=[],
                legend_mode="suppressed",
                title_block_mode="embedded",
            )
        )
    if bac_pfd_mode:
        _apply_bac_pfd_stitching_metadata(sheets, module_map)
    for connection in semantics.connections:
        source_module = next((module for module in modules.modules if connection.source_entity_id in module.entity_ids), None)
        target_module = next((module for module in modules.modules if connection.target_entity_id in module.entity_ids), None)
        if source_module is None or target_module is None:
            continue
        source_sheet_id = module_to_sheet.get(source_module.module_id)
        target_sheet_id = module_to_sheet.get(target_module.module_id)
        if not source_sheet_id or source_sheet_id != target_sheet_id:
            continue
        source_port_id = f"{source_module.module_id}__{connection.connection_id}__out"
        target_port_id = f"{target_module.module_id}__{connection.connection_id}__in"
        for sheet in sheets:
            if sheet.sheet_id == source_sheet_id:
                sheet.connectors.append(
                    DiagramInterModuleConnector(
                        connector_id=f"sheet_connector_{connection.connection_id}",
                        role=connection.role,
                        source_module_id=source_module.module_id,
                        source_port_id=source_port_id,
                        target_module_id=target_module.module_id,
                        target_port_id=target_port_id,
                        label=connection.label,
                        continuation_marker="",
                    )
                )
                break
    markdown = (
        "### PFD Sheet Composition\n\n"
        f"- Sheets: {len(sheets)}\n"
        f"- Section modules placed: {sum(len(sheet.module_placements) for sheet in sheets)}\n"
    )
    if bac_pfd_mode:
        stitched_panels = " | ".join(
            sheet.stitch_panel_title or sheet.title
            for sheet in sheets
        )
        markdown += f"- BAC stitched panels: {stitched_panels}\n"
    return DiagramSheetCompositionArtifact(
        diagram_id=modules.diagram_id.replace("_modules", "_sheet_composition"),
        route_id=modules.route_id,
        diagram_level=DiagramLevel.PFD,
        sheets=sheets,
        citations=modules.citations,
        assumptions=modules.assumptions + ["PFD sheet composition places section modules across one or more sheets before final SVG rendering."],
        markdown=markdown,
    )


def _build_bac_pfd_sheet_composition(
    modules: DiagramModuleArtifact,
    style: DiagramStyleProfile,
) -> DiagramSheetCompositionArtifact:
    module_map = {module.module_id: module for module in modules.modules}
    section_to_module = {module.section_id: module for module in modules.modules}
    panel_specs = [
        (
            "sheet_1",
            "BAC PFD Panel 1: Feed, Reaction, and Cleanup",
            1500,
            760,
            [
                ("feed", 84.0, 186.0, 248.0, 214.0),
                ("reaction", 364.0, 148.0, 282.0, 244.0),
                ("cleanup", 684.0, 150.0, 262.0, 228.0),
                ("concentration", 984.0, 150.0, 248.0, 228.0),
            ],
            "bac-pfd-panel-1",
        ),
        (
            "sheet_2",
            "BAC PFD Panel 2: Purification, Storage, and Offsites",
            1420,
            720,
            [
                ("purification", 92.0, 150.0, 292.0, 262.0),
                ("storage", 492.0, 150.0, 238.0, 220.0),
                ("waste_treatment", 842.0, 150.0, 238.0, 220.0),
            ],
            "bac-pfd-panel-2",
        ),
    ]
    sheets: list[DiagramSheetComposition] = []
    for index, (sheet_id, title, width_px, height_px, placements, panel_id) in enumerate(panel_specs, start=1):
        module_placements: list[DiagramModulePlacement] = []
        z_index = 1
        for section_id, x, y, width, height in placements:
            module = section_to_module.get(section_id)
            if module is None:
                continue
            module_placements.append(
                DiagramModulePlacement(
                    module_id=module.module_id,
                    sheet_id=sheet_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    z_index=z_index,
                )
            )
            z_index += 1
        if not module_placements:
            continue
        sheets.append(
            DiagramSheetComposition(
                sheet_id=sheet_id,
                title=title,
                diagram_level=DiagramLevel.PFD,
                width_px=width_px,
                height_px=height_px,
                module_placements=module_placements,
                connectors=[],
                legend_mode="suppressed",
                title_block_mode="embedded",
                stitch_panel_id=panel_id,
                stitch_panel_title=title,
                stitch_prev_sheet_id=f"sheet_{index - 1}" if index > 1 else "",
                stitch_next_sheet_id=f"sheet_{index + 1}" if index < len(panel_specs) else "",
            )
        )
    markdown = (
        "### PFD Sheet Composition\n\n"
        f"- Sheets: {len(sheets)}\n"
        "- BAC PFD uses fixed drafted panels instead of generic module packing.\n"
    )
    return DiagramSheetCompositionArtifact(
        diagram_id=modules.diagram_id.replace("_modules", "_sheet_composition"),
        route_id=modules.route_id,
        diagram_level=DiagramLevel.PFD,
        sheets=sheets,
        citations=modules.citations,
        assumptions=modules.assumptions + ["BAC PFD panels use fixed section placement to preserve a compact drafted appearance."],
        markdown=markdown,
    )


def _apply_bac_pfd_stitching_metadata(
    sheets: list[DiagramSheetComposition],
    module_map: dict[str, DiagramModuleSpec],
) -> None:
    panel_profiles = [
        (
            "bac-pfd-panel-1",
            "BAC PFD Panel 1: Feed, Reaction, and Cleanup",
            ("feed", "reaction", "cleanup", "concentration"),
        ),
        (
            "bac-pfd-panel-2",
            "BAC PFD Panel 2: Purification, Storage, and Offsites",
            ("purification", "storage", "waste_treatment"),
        ),
    ]
    for index, sheet in enumerate(sheets):
        section_ids = {
            module_map[placement.module_id].section_id
            for placement in sheet.module_placements
            if placement.module_id in module_map
        }
        chosen_panel_id = f"bac-pfd-panel-{index + 1}"
        chosen_title = f"BAC PFD Panel {index + 1}"
        best_score = -1
        for panel_id, panel_title, profile_sections in panel_profiles:
            score = len(section_ids.intersection(profile_sections))
            if score > best_score:
                best_score = score
                chosen_panel_id = panel_id
                chosen_title = panel_title
        sheet.title = chosen_title
        sheet.stitch_panel_id = chosen_panel_id
        sheet.stitch_panel_title = chosen_title
        if index > 0:
            sheet.stitch_prev_sheet_id = sheets[index - 1].sheet_id
        if index + 1 < len(sheets):
            sheet.stitch_next_sheet_id = sheets[index + 1].sheet_id


def _apply_bac_pid_stitching_metadata(sheets: list[DiagramSheetComposition]) -> None:
    ordered_sheets = sorted(sheets, key=lambda item: item.sheet_id)
    for index, sheet in enumerate(ordered_sheets, start=1):
        panel_title = f"BAC P&ID Panel {index}: {sheet.title}"
        sheet.stitch_panel_id = f"bac-pid-panel-{index}"
        sheet.stitch_panel_title = panel_title
        if index > 1:
            sheet.stitch_prev_sheet_id = ordered_sheets[index - 2].sheet_id
        if index < len(ordered_sheets):
            sheet.stitch_next_sheet_id = ordered_sheets[index].sheet_id


def _plan_pfd_sheet_module_chunks(
    module_order: list[str],
    module_sizes: dict[str, tuple[float, float]],
    *,
    modules_per_sheet: int,
    row_width_budget: float,
    sheet_height_budget: float,
    horizontal_gap: float,
    row_gap: float,
) -> list[list[str]]:
    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    current_row: list[str] = []
    row_width = 0.0
    chunk_height = 160.0
    for module_id in module_order:
        width, height = module_sizes[module_id]
        proposed_row_width = width if not current_row else row_width + horizontal_gap + width
        proposed_row_height = max((module_sizes[item][1] for item in current_row + [module_id]), default=height)
        current_row_height = max((module_sizes[item][1] for item in current_row), default=0.0)
        row_would_wrap = current_row and proposed_row_width > row_width_budget
        chunk_would_overflow_height = (
            row_would_wrap
            and current_chunk
            and chunk_height + row_gap + proposed_row_height > sheet_height_budget - 120.0
        )
        chunk_would_overflow_count = len(current_chunk) >= modules_per_sheet
        if chunk_would_overflow_height or chunk_would_overflow_count:
            chunks.append(current_chunk)
            current_chunk = []
            current_row = []
            row_width = 0.0
            chunk_height = 160.0
            proposed_row_width = width
            proposed_row_height = height
            row_would_wrap = False
            current_row_height = 0.0
        if row_would_wrap:
            chunk_height += current_row_height + row_gap
            current_row = []
            row_width = 0.0
            proposed_row_width = width
        current_chunk.append(module_id)
        current_row.append(module_id)
        row_width = proposed_row_width
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def _pack_pfd_modules_for_sheet(
    module_ids: list[str],
    module_sizes: dict[str, tuple[float, float]],
    *,
    row_width_budget: float,
    horizontal_gap: float,
) -> list[list[str]]:
    rows: list[list[str]] = []
    current_row: list[str] = []
    current_width = 0.0
    for module_id in module_ids:
        width, _ = module_sizes[module_id]
        proposed_width = width if not current_row else current_width + horizontal_gap + width
        if current_row and proposed_width > row_width_budget:
            rows.append(current_row)
            current_row = [module_id]
            current_width = width
        else:
            current_row.append(module_id)
            current_width = proposed_width
    if current_row:
        rows.append(current_row)
    return rows


def build_control_system_semantics(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    flowsheet_graph: FlowsheetGraph,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> PlantDiagramSemanticsArtifact:
    del symbol_library
    entities: list[PlantDiagramEntity] = []
    connections: list[PlantDiagramConnection] = []
    unit_label_by_id = {node.node_id: node.label for node in flowsheet_graph.nodes}
    seen_unit_ids: set[str] = set()
    section_order: list[str] = []

    for unit_id in control_architecture.critical_units:
        if unit_id not in seen_unit_ids:
            seen_unit_ids.add(unit_id)
            unit_node = next((node for node in flowsheet_graph.nodes if node.node_id == unit_id), None)
            section_id = unit_node.section_id if unit_node is not None else "control"
            if section_id and section_id not in section_order:
                section_order.append(section_id)
            entities.append(
                PlantDiagramEntity(
                    entity_id=f"ctrl_unit_{unit_id}",
                    kind=DiagramEntityKind.UNIT,
                    label=unit_label_by_id.get(unit_id, unit_id),
                    diagram_level=DiagramLevel.CONTROL,
                    section_id=section_id,
                    unit_id=unit_id,
                    symbol_key="control_unit_ref",
                    preferred_module_id=f"control_module_{re.sub(r'[^a-z0-9]+', '_', unit_id.lower()).strip('_')}",
                )
            )

    for loop in control_plan.control_loops:
        unit_entity_id = f"ctrl_unit_{loop.unit_id}" if loop.unit_id else ""
        if loop.unit_id and loop.unit_id not in seen_unit_ids:
            seen_unit_ids.add(loop.unit_id)
            unit_node = next((node for node in flowsheet_graph.nodes if node.node_id == loop.unit_id), None)
            section_id = unit_node.section_id if unit_node is not None else "control"
            if section_id and section_id not in section_order:
                section_order.append(section_id)
            entities.append(
                PlantDiagramEntity(
                    entity_id=unit_entity_id,
                    kind=DiagramEntityKind.UNIT,
                    label=unit_label_by_id.get(loop.unit_id, loop.unit_id),
                    diagram_level=DiagramLevel.CONTROL,
                    section_id=section_id,
                    unit_id=loop.unit_id,
                    symbol_key="control_unit_ref",
                    preferred_module_id=f"control_module_{re.sub(r'[^a-z0-9]+', '_', loop.unit_id.lower()).strip('_')}",
                )
            )
        loop_entity_id = f"ctrl_loop_{loop.control_id}"
        instrument_entity_id = f"ctrl_instr_{loop.control_id}"
        entities.append(
            PlantDiagramEntity(
                entity_id=loop_entity_id,
                kind=DiagramEntityKind.CONTROL_LOOP,
                label=loop.control_id,
                diagram_level=DiagramLevel.CONTROL,
                section_id=next((entity.section_id for entity in entities if entity.entity_id == unit_entity_id), "control"),
                control_id=loop.control_id,
                symbol_key="control_loop",
                preferred_module_id=f"control_module_{re.sub(r'[^a-z0-9]+', '_', (loop.unit_id or loop.control_id).lower()).strip('_')}",
                metadata={"criticality": loop.criticality or ""},
            )
        )
        entities.append(
            PlantDiagramEntity(
                entity_id=instrument_entity_id,
                kind=DiagramEntityKind.INSTRUMENT,
                label=loop.sensor,
                diagram_level=DiagramLevel.CONTROL,
                section_id=next((entity.section_id for entity in entities if entity.entity_id == unit_entity_id), "control"),
                control_id=loop.control_id,
                instrument_id=loop.sensor,
                symbol_key="control_instrument",
                preferred_module_id=f"control_module_{re.sub(r'[^a-z0-9]+', '_', (loop.unit_id or loop.control_id).lower()).strip('_')}",
            )
        )
        if unit_entity_id:
            connections.append(
                PlantDiagramConnection(
                    connection_id=f"ctrl_conn_unit_loop_{loop.control_id}",
                    role=DiagramEdgeRole.CONTROL_SIGNAL,
                    diagram_level=DiagramLevel.CONTROL,
                    source_entity_id=unit_entity_id,
                    target_entity_id=loop_entity_id,
                    control_id=loop.control_id,
                    label=loop.controlled_variable,
                    preferred_lane="control_signal",
                )
            )
        connections.append(
            PlantDiagramConnection(
                connection_id=f"ctrl_conn_loop_instr_{loop.control_id}",
                role=DiagramEdgeRole.CONTROL_SIGNAL,
                diagram_level=DiagramLevel.CONTROL,
                source_entity_id=loop_entity_id,
                target_entity_id=instrument_entity_id,
                control_id=loop.control_id,
                label=loop.sensor,
                preferred_lane="control_signal",
            )
        )
        if loop.safeguard_linkage:
            connections.append(
                PlantDiagramConnection(
                    connection_id=f"ctrl_conn_safeguard_{loop.control_id}",
                    role=DiagramEdgeRole.SAFEGUARD,
                    diagram_level=DiagramLevel.CONTROL,
                    source_entity_id=loop_entity_id,
                    target_entity_id=unit_entity_id or instrument_entity_id,
                    control_id=loop.control_id,
                    label=loop.safeguard_linkage,
                    preferred_lane="safeguard",
                )
            )

    markdown = (
        "### Control Semantics\n\n"
        f"- Entities: {len(entities)}\n"
        f"- Connections: {len(connections)}\n"
    )
    return PlantDiagramSemanticsArtifact(
        diagram_id=f"{flowsheet_graph.route_id}_control_semantics",
        route_id=flowsheet_graph.route_id,
        entities=entities,
        connections=connections,
        section_order=section_order,
        citations=sorted(set(control_plan.citations + control_architecture.citations + flowsheet_graph.citations)),
        assumptions=control_plan.assumptions + control_architecture.assumptions + flowsheet_graph.assumptions + ["Control semantics isolate loop structure before architecture rendering."],
        markdown=markdown,
    )


def build_control_system_modules(
    semantics: PlantDiagramSemanticsArtifact,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> DiagramModuleArtifact:
    level_policy = next(policy for policy in symbol_library.level_policies if policy.diagram_level == DiagramLevel.CONTROL)
    module_ids = sorted({entity.preferred_module_id for entity in semantics.entities if entity.preferred_module_id})
    modules: list[DiagramModuleSpec] = []
    for module_id in module_ids:
        module_entities = [entity for entity in semantics.entities if entity.preferred_module_id == module_id]
        entity_ids = {entity.entity_id for entity in module_entities}
        section_id = next((entity.section_id for entity in module_entities if entity.section_id), "control")
        touching_connections = [
            connection
            for connection in semantics.connections
            if connection.source_entity_id in entity_ids or connection.target_entity_id in entity_ids
        ]
        boundary_ports: list[DiagramModulePort] = []
        seen_ports: set[str] = set()
        for connection in touching_connections:
            for direction, entity_id in (("out", connection.source_entity_id), ("in", connection.target_entity_id)):
                if entity_id not in entity_ids:
                    continue
                port_id = f"{module_id}__{connection.connection_id}__{direction}"
                if port_id in seen_ports:
                    continue
                side = DiagramPortSide.RIGHT if direction == "out" else DiagramPortSide.LEFT
                if connection.role == DiagramEdgeRole.SAFEGUARD:
                    side = DiagramPortSide.TOP if direction == "out" else DiagramPortSide.BOTTOM
                boundary_ports.append(
                    DiagramModulePort(
                        port_id=port_id,
                        entity_id=entity_id,
                        connection_role=connection.role,
                        side=side,
                        order_index=len(boundary_ports) + 1,
                        lane=connection.preferred_lane,
                        label=connection.label,
                    )
                )
                seen_ports.add(port_id)
        modules.append(
            DiagramModuleSpec(
                module_id=module_id,
                module_kind=DiagramLevel.CONTROL,
                title=module_id.replace("control_module_", "").upper(),
                symbol_policy=level_policy.symbol_policy,
                section_id=section_id,
                unit_ids=[entity.unit_id for entity in module_entities if entity.unit_id],
                entity_ids=[entity.entity_id for entity in module_entities],
                connection_ids=[connection.connection_id for connection in touching_connections],
                boundary_ports=boundary_ports,
                allowed_edge_roles=level_policy.allowed_edge_roles,
                forbidden_entity_kinds=level_policy.forbidden_entity_kinds,
                preferred_orientation="TB",
                sheet_break_allowed=True,
                constraints=[
                    DiagramModuleConstraint(key="min_node_spacing_px", value=str(level_policy.minimum_node_spacing_px)),
                    DiagramModuleConstraint(key="min_label_clearance_px", value=str(level_policy.minimum_label_clearance_px)),
                    DiagramModuleConstraint(key="orthogonal_only", value="true"),
                ],
                notes=[f"Control module for {module_id}."],
            )
        )
    markdown = (
        "### Control Modules\n\n"
        f"- Modules: {len(modules)}\n"
        "- Each module groups one controlled unit with its principal loop and instrument references.\n"
    )
    return DiagramModuleArtifact(
        diagram_id=semantics.diagram_id.replace("_semantics", "_modules"),
        route_id=semantics.route_id,
        module_kind=DiagramLevel.CONTROL,
        modules=modules,
        citations=semantics.citations,
        assumptions=semantics.assumptions + ["Control modules isolate per-unit loop clusters before rendering."],
        markdown=markdown,
    )


def build_control_system_sheet_composition(
    modules: DiagramModuleArtifact,
    style: DiagramStyleProfile,
) -> DiagramSheetCompositionArtifact:
    placements: list[DiagramModulePlacement] = []
    x_cursor = 110.0
    y_base = 140.0
    for z_index, module in enumerate(modules.modules[:6], start=1):
        width = 240.0
        height = 190.0
        placements.append(
            DiagramModulePlacement(
                module_id=module.module_id,
                sheet_id="sheet_1",
                x=x_cursor,
                y=y_base,
                width=width,
                height=height,
                z_index=z_index,
            )
        )
        x_cursor += width + 54.0
    sheet_1 = DiagramSheetComposition(
        sheet_id="sheet_1",
        title="Process Control Architecture",
        diagram_level=DiagramLevel.CONTROL,
        width_px=max(style.canvas_width_px, int((max((placement.x + placement.width) for placement in placements) if placements else 0) + 160)),
        height_px=max(style.canvas_height_px, 980),
        module_placements=placements,
        connectors=[],
        legend_mode="embedded",
        title_block_mode="embedded",
    )
    overlay_placements = [
        DiagramModulePlacement(
            module_id=module.module_id,
            sheet_id="sheet_2",
            x=120.0 + (index % 3) * 280.0,
            y=170.0 + (index // 3) * 220.0,
            width=230.0,
            height=170.0,
            z_index=index + 1,
        )
        for index, module in enumerate(modules.modules[:6])
    ]
    sheet_2 = DiagramSheetComposition(
        sheet_id="sheet_2",
        title="Instrumented Process Flow Overlay",
        diagram_level=DiagramLevel.CONTROL,
        width_px=max(style.canvas_width_px, 1700),
        height_px=max(style.canvas_height_px, 940),
        module_placements=overlay_placements,
        connectors=[],
        legend_mode="embedded",
        title_block_mode="embedded",
    )
    interlock_placements = [
        DiagramModulePlacement(
            module_id=module.module_id,
            sheet_id="sheet_3",
            x=120.0 + (index % 2) * 760.0,
            y=150.0 + (index // 2) * 230.0,
            width=640.0,
            height=180.0,
            z_index=index + 1,
        )
        for index, module in enumerate(modules.modules[:6])
    ]
    sheet_3 = DiagramSheetComposition(
        sheet_id="sheet_3",
        title="Interlocks and Permissives",
        diagram_level=DiagramLevel.CONTROL,
        width_px=max(style.canvas_width_px, 1760),
        height_px=max(style.canvas_height_px, 980),
        module_placements=interlock_placements,
        connectors=[],
        legend_mode="embedded",
        title_block_mode="embedded",
    )
    shutdown_placements = [
        DiagramModulePlacement(
            module_id=module.module_id,
            sheet_id="sheet_4",
            x=120.0 + (index % 2) * 760.0,
            y=150.0 + (index // 2) * 210.0,
            width=640.0,
            height=160.0,
            z_index=index + 1,
        )
        for index, module in enumerate(modules.modules[:6])
    ]
    sheet_4 = DiagramSheetComposition(
        sheet_id="sheet_4",
        title="Shutdowns and Protective Trips",
        diagram_level=DiagramLevel.CONTROL,
        width_px=max(style.canvas_width_px, 1760),
        height_px=max(style.canvas_height_px, 920),
        module_placements=shutdown_placements,
        connectors=[],
        legend_mode="embedded",
        title_block_mode="embedded",
    )
    markdown = (
        "### Control Sheet Composition\n\n"
        f"- Sheets: 4\n"
        f"- Architecture modules placed: {len(placements)}\n"
    )
    return DiagramSheetCompositionArtifact(
        diagram_id=modules.diagram_id.replace("_modules", "_sheet_composition"),
        route_id=modules.route_id,
        diagram_level=DiagramLevel.CONTROL,
        sheets=[sheet_1, sheet_2, sheet_3, sheet_4],
        citations=modules.citations,
        assumptions=modules.assumptions + ["Control sheet composition places supervisory architecture, overlay, interlock/permissive, and shutdown review views on separate sheets."],
        markdown=markdown,
    )


def build_pid_lite_semantics(
    flowsheet_graph: FlowsheetGraph,
    stream_table: StreamTable,
    control_plan: ControlPlanArtifact,
    symbol_library: DiagramSymbolLibraryArtifact,
    target: DiagramTargetProfile | None = None,
) -> PlantDiagramSemanticsArtifact:
    del symbol_library
    equipment_templates = build_diagram_equipment_templates()
    entities: list[PlantDiagramEntity] = []
    connections: list[PlantDiagramConnection] = []
    unit_node_by_id = {node.node_id: node for node in flowsheet_graph.nodes}
    streams_by_unit: dict[str, list] = {}
    for stream in stream_table.streams:
        for unit_id in filter(None, [stream.source_unit_id, stream.destination_unit_id]):
            streams_by_unit.setdefault(unit_id, []).append(stream)

    loops_by_unit: dict[str, list] = {}
    for loop in control_plan.control_loops:
        if loop.unit_id:
            loops_by_unit.setdefault(loop.unit_id, []).append(loop)
    if target is not None and _is_bac_target(target):
        for unit_id in _bac_pid_required_unit_ids(flowsheet_graph):
            loops_by_unit.setdefault(unit_id, [])

    section_order: list[str] = []
    for unit_id, loops in loops_by_unit.items():
        unit_node = unit_node_by_id.get(unit_id)
        section_id = unit_node.section_id if unit_node is not None else "pid_cluster"
        if section_id and section_id not in section_order:
            section_order.append(section_id)
        module_id = f"pid_module_{re.sub(r'[^a-z0-9]+', '_', unit_id.lower()).strip('_')}"
        unit_entity_id = f"pid_unit_{re.sub(r'[^a-z0-9]+', '_', unit_id.lower()).strip('_')}"
        template = _equipment_template_for_text(
            unit_node.unit_type if unit_node is not None else "",
            unit_node.label if unit_node is not None else unit_id,
            equipment_templates,
        )
        entities.append(
            PlantDiagramEntity(
                entity_id=unit_entity_id,
                kind=DiagramEntityKind.UNIT,
                label=unit_node.label if unit_node is not None else unit_id,
                diagram_level=DiagramLevel.PID_LITE,
                section_id=section_id,
                unit_id=unit_id,
                equipment_tag=unit_id,
                service=unit_node.label if unit_node is not None else unit_id,
                symbol_key="pid_unit",
                preferred_module_id=module_id,
                must_be_isolated=True,
                metadata={
                    "unit_type": unit_node.unit_type if unit_node is not None else "",
                    "template_id": template.template_id,
                    "template_family": template.family,
                    "bac_pid_profile": "true" if target is not None and _is_bac_target(target) else "",
                },
            )
        )

        for stream_index, stream in enumerate(streams_by_unit.get(unit_id, [])[:2], start=1):
            valve_symbol = "pid_manual_valve"
            valve_function = "isolation_valve"
            if stream.source_unit_id == unit_id and stream.stream_role in {"intermediate", "product"}:
                valve_symbol = "pid_control_valve"
                valve_function = "line_control_valve"
            valve_entity_id = f"{unit_entity_id}_line_valve_{stream_index}"
            entities.append(
                PlantDiagramEntity(
                    entity_id=valve_entity_id,
                    kind=DiagramEntityKind.VALVE,
                    label=f"XV-{unit_id[-3:]}-{stream_index}",
                    diagram_level=DiagramLevel.PID_LITE,
                    section_id=section_id,
                    symbol_key=valve_symbol,
                    preferred_module_id=module_id,
                    must_be_isolated=True,
                    attached_to_entity_id=unit_entity_id,
                    attachment_role="process_line",
                    pid_function=valve_function,
                )
            )
            connections.append(
                PlantDiagramConnection(
                    connection_id=f"{unit_entity_id}_line_{stream_index}",
                    role=DiagramEdgeRole.PRODUCT if stream.stream_role == "product" else DiagramEdgeRole.PROCESS,
                    diagram_level=DiagramLevel.PID_LITE,
                    source_entity_id=unit_entity_id,
                    target_entity_id=valve_entity_id,
                    stream_id=stream.stream_id,
                    label=_pfd_stream_label(stream.stream_id, stream.description, stream.stream_role),
                    preferred_lane="process_line",
                    line_class=_pid_line_class_for_stream(stream),
                )
            )

        for loop_index, loop in enumerate(loops, start=1):
            loop_slug = re.sub(r"[^a-z0-9]+", "_", loop.control_id.lower()).strip("_")
            variable_slug = re.sub(r"[^a-z0-9]+", "_", loop.controlled_variable.lower()).strip("_") or "process"
            transmitter_entity_id = f"pid_{loop_slug}_tx"
            indicator_entity_id = f"pid_{loop_slug}_ind"
            controller_entity_id = f"pid_{loop_slug}_ctrl"
            valve_entity_id = f"pid_{loop_slug}_cv"
            entities.extend(
                [
                    PlantDiagramEntity(
                        entity_id=transmitter_entity_id,
                        kind=DiagramEntityKind.INSTRUMENT,
                        label=loop.sensor,
                        diagram_level=DiagramLevel.PID_LITE,
                        section_id=section_id,
                        control_id=loop.control_id,
                        instrument_id=loop.sensor,
                        symbol_key="pid_transmitter",
                        preferred_module_id=module_id,
                        must_be_isolated=True,
                        attached_to_entity_id=unit_entity_id,
                        attachment_role="measurement",
                        pid_function=f"{variable_slug}_transmitter",
                        pid_loop_id=loop.control_id,
                    ),
                    PlantDiagramEntity(
                        entity_id=indicator_entity_id,
                        kind=DiagramEntityKind.INSTRUMENT,
                        label=f"{loop.sensor}-IND",
                        diagram_level=DiagramLevel.PID_LITE,
                        section_id=section_id,
                        control_id=loop.control_id,
                        instrument_id=f"{loop.sensor}-IND",
                        symbol_key="pid_indicator",
                        preferred_module_id=module_id,
                        must_be_isolated=True,
                        attached_to_entity_id=unit_entity_id,
                        attachment_role="local_indication",
                        pid_function=f"{variable_slug}_indicator",
                        pid_loop_id=loop.control_id,
                    ),
                    PlantDiagramEntity(
                        entity_id=controller_entity_id,
                        kind=DiagramEntityKind.INSTRUMENT,
                        label=loop.control_id,
                        diagram_level=DiagramLevel.PID_LITE,
                        section_id=section_id,
                        control_id=loop.control_id,
                        instrument_id=loop.control_id,
                        symbol_key="pid_controller",
                        preferred_module_id=module_id,
                        must_be_isolated=True,
                        attached_to_entity_id=unit_entity_id,
                        attachment_role="local_control",
                        pid_function=f"{variable_slug}_controller",
                        pid_loop_id=loop.control_id,
                    ),
                    PlantDiagramEntity(
                        entity_id=valve_entity_id,
                        kind=DiagramEntityKind.VALVE,
                        label=loop.actuator,
                        diagram_level=DiagramLevel.PID_LITE,
                        section_id=section_id,
                        control_id=loop.control_id,
                        symbol_key="pid_control_valve",
                        preferred_module_id=module_id,
                        must_be_isolated=True,
                        attached_to_entity_id=unit_entity_id,
                        attachment_role="final_control_element",
                        pid_function=_pid_function_for_actuator(loop.actuator),
                        pid_loop_id=loop.control_id,
                    ),
                ]
            )
            connections.extend(
                [
                    PlantDiagramConnection(
                        connection_id=f"pid_{loop_slug}_sig_tx_ind",
                        role=DiagramEdgeRole.CONTROL_SIGNAL,
                        diagram_level=DiagramLevel.PID_LITE,
                        source_entity_id=transmitter_entity_id,
                        target_entity_id=indicator_entity_id,
                        control_id=loop.control_id,
                        label="local indication",
                        preferred_lane="signal",
                    ),
                    PlantDiagramConnection(
                        connection_id=f"pid_{loop_slug}_sig_tx_ctrl",
                        role=DiagramEdgeRole.CONTROL_SIGNAL,
                        diagram_level=DiagramLevel.PID_LITE,
                        source_entity_id=transmitter_entity_id,
                        target_entity_id=controller_entity_id,
                        control_id=loop.control_id,
                        label=loop.controlled_variable,
                        preferred_lane="signal",
                    ),
                    PlantDiagramConnection(
                        connection_id=f"pid_{loop_slug}_sig_ctrl_cv",
                        role=DiagramEdgeRole.CONTROL_SIGNAL,
                        diagram_level=DiagramLevel.PID_LITE,
                        source_entity_id=controller_entity_id,
                        target_entity_id=valve_entity_id,
                        control_id=loop.control_id,
                        label=loop.manipulated_variable,
                        preferred_lane="signal",
                    ),
                    PlantDiagramConnection(
                        connection_id=f"pid_{loop_slug}_line_unit_cv",
                        role=DiagramEdgeRole.PROCESS,
                        diagram_level=DiagramLevel.PID_LITE,
                        source_entity_id=unit_entity_id,
                        target_entity_id=valve_entity_id,
                        control_id=loop.control_id,
                        label=loop.manipulated_variable,
                        preferred_lane="process_line",
                        line_class=_pid_line_class_for_variable(loop.manipulated_variable),
                    ),
                ]
            )
            if loop.safeguard_linkage:
                relief_entity_id = f"pid_{loop_slug}_psv"
                entities.append(
                    PlantDiagramEntity(
                        entity_id=relief_entity_id,
                        kind=DiagramEntityKind.VALVE,
                        label=f"PSV-{loop_index:03d}",
                        diagram_level=DiagramLevel.PID_LITE,
                        section_id=section_id,
                        control_id=loop.control_id,
                        symbol_key="pid_relief_valve",
                        preferred_module_id=module_id,
                        must_be_isolated=True,
                        attached_to_entity_id=unit_entity_id,
                        attachment_role="safeguard_relief",
                        pid_function="pressure_relief_valve",
                    )
                )
                connections.append(
                    PlantDiagramConnection(
                        connection_id=f"pid_{loop_slug}_safeguard_relief",
                        role=DiagramEdgeRole.SAFEGUARD,
                        diagram_level=DiagramLevel.PID_LITE,
                        source_entity_id=unit_entity_id,
                        target_entity_id=relief_entity_id,
                        control_id=loop.control_id,
                        label=loop.safeguard_linkage,
                        preferred_lane="safeguard",
                    )
                )

        if target is not None and _is_bac_target(target) and not loops:
            if _bac_pid_requires_relief(unit_node):
                relief_entity_id = f"{unit_entity_id}_psv"
                entities.append(
                    PlantDiagramEntity(
                        entity_id=relief_entity_id,
                        kind=DiagramEntityKind.VALVE,
                        label=f"PSV-{unit_id[-3:]}",
                        diagram_level=DiagramLevel.PID_LITE,
                        section_id=section_id,
                        unit_id=unit_id,
                        symbol_key="pid_relief_valve",
                        preferred_module_id=module_id,
                        must_be_isolated=True,
                        attached_to_entity_id=unit_entity_id,
                        attachment_role="safeguard_relief",
                        pid_function="pressure_relief_valve",
                    )
                )
                connections.append(
                    PlantDiagramConnection(
                        connection_id=f"{unit_entity_id}_safeguard_relief",
                        role=DiagramEdgeRole.SAFEGUARD,
                        diagram_level=DiagramLevel.PID_LITE,
                        source_entity_id=unit_entity_id,
                        target_entity_id=relief_entity_id,
                        unit_id=unit_id,
                        label="General overpressure protection",
                        preferred_lane="safeguard",
                    )
                )

    markdown = (
        "### P&ID-lite Semantics\n\n"
        f"- Unit-cluster entities: {len(entities)}\n"
        f"- Local cluster connections: {len(connections)}\n"
    )
    return PlantDiagramSemanticsArtifact(
        diagram_id=f"{flowsheet_graph.route_id}_pid_lite_semantics",
        route_id=flowsheet_graph.route_id,
        entities=entities,
        connections=connections,
        section_order=section_order,
        citations=sorted(set(flowsheet_graph.citations + stream_table.citations + control_plan.citations)),
        assumptions=flowsheet_graph.assumptions
        + stream_table.assumptions
        + control_plan.assumptions
        + ["P&ID-lite semantics isolate local unit clusters with attached valves, transmitters, indicators, controllers, and safeguards."],
        markdown=markdown,
    )


def build_pid_lite_modules(
    semantics: PlantDiagramSemanticsArtifact,
    symbol_library: DiagramSymbolLibraryArtifact,
) -> DiagramModuleArtifact:
    level_policy = next(policy for policy in symbol_library.level_policies if policy.diagram_level == DiagramLevel.PID_LITE)
    modules: list[DiagramModuleSpec] = []
    connection_lookup = {connection.connection_id: connection for connection in semantics.connections}
    module_ids = sorted({entity.preferred_module_id for entity in semantics.entities if entity.preferred_module_id})
    for module_id in module_ids:
        module_entities = [entity for entity in semantics.entities if entity.preferred_module_id == module_id]
        if not module_entities:
            continue
        section_id = next((entity.section_id for entity in module_entities if entity.section_id), "pid_cluster")
        unit_label = next((entity.label for entity in module_entities if entity.kind == DiagramEntityKind.UNIT), module_id.replace("pid_module_", "").upper())
        unit_entities = [entity for entity in module_entities if entity.kind == DiagramEntityKind.UNIT]
        if not unit_entities:
            continue
        unit_entity = unit_entities[0]
        bac_pid_mode = unit_entity.metadata.get("bac_pid_profile", "") == "true"
        attachment_entities = [entity for entity in module_entities if entity.entity_id != unit_entity.entity_id]
        groups: list[list[PlantDiagramEntity]] = []
        grouped_loop_ids: set[str] = set()
        process_line_entities: list[PlantDiagramEntity] = []
        other_entities: list[PlantDiagramEntity] = []
        for entity in attachment_entities:
            if entity.pid_loop_id:
                if entity.pid_loop_id in grouped_loop_ids:
                    continue
                loop_group = [
                    candidate
                    for candidate in attachment_entities
                    if candidate.pid_loop_id == entity.pid_loop_id
                ]
                groups.append(loop_group)
                grouped_loop_ids.add(entity.pid_loop_id)
            elif (entity.attachment_role or "") == "process_line":
                process_line_entities.append(entity)
            else:
                other_entities.append(entity)
        groups.extend([[entity] for entity in process_line_entities])
        groups.extend([[entity] for entity in other_entities])

        max_nodes = 12
        group_chunks: list[list[PlantDiagramEntity]] = []
        current_chunk: list[PlantDiagramEntity] = []
        current_count = 1  # reserve the shared unit anchor
        for group in groups:
            if current_chunk and current_count + len(group) > max_nodes:
                group_chunks.append(current_chunk)
                current_chunk = []
                current_count = 1
            current_chunk.extend(group)
            current_count += len(group)
        if current_chunk or not groups:
            group_chunks.append(current_chunk)

        split_views = len(group_chunks) > 1
        for view_index, chunk in enumerate(group_chunks, start=1):
            chunk_entities = [unit_entity, *chunk]
            chunk_entity_ids = {entity.entity_id for entity in chunk_entities}
            chunk_connections = [
                connection
                for connection_id, connection in connection_lookup.items()
                if connection.source_entity_id in chunk_entity_ids and connection.target_entity_id in chunk_entity_ids
            ]
            chunk_module_id = module_id if not split_views else f"{module_id}_view_{view_index}"
            title = _pid_lite_sheet_title(unit_label, section_id, bac_pid_mode=bac_pid_mode)
            if split_views:
                title = f"{title} (View {view_index})"
            notes = ["P&ID-lite cluster module for local instrumentation, valve, and safeguard detail."]
            if split_views:
                notes.append("Split view generated to keep a dense local unit cluster readable.")
            modules.append(
                DiagramModuleSpec(
                    module_id=chunk_module_id,
                    module_kind=DiagramLevel.PID_LITE,
                    title=title,
                    symbol_policy=level_policy.symbol_policy,
                    section_id=section_id,
                    unit_ids=[entity.unit_id for entity in chunk_entities if entity.kind == DiagramEntityKind.UNIT and entity.unit_id],
                    entity_ids=[entity.entity_id for entity in chunk_entities],
                    connection_ids=[connection.connection_id for connection in chunk_connections],
                    boundary_ports=[],
                    allowed_edge_roles=level_policy.allowed_edge_roles,
                    forbidden_entity_kinds=level_policy.forbidden_entity_kinds,
                    preferred_orientation="TB",
                    sheet_break_allowed=True,
                    must_be_isolated=True,
                    constraints=[
                        DiagramModuleConstraint(key="min_node_spacing_px", value=str(level_policy.minimum_node_spacing_px)),
                        DiagramModuleConstraint(key="min_label_clearance_px", value=str(level_policy.minimum_label_clearance_px)),
                        DiagramModuleConstraint(key="max_nodes", value=str(max_nodes)),
                        DiagramModuleConstraint(key="orthogonal_only", value="true"),
                    ],
                    notes=notes,
                )
            )
    markdown = (
        "### P&ID-lite Modules\n\n"
        f"- Unit-cluster modules: {len(modules)}\n"
        "- Each module isolates one local equipment cluster with its attached instruments and valves.\n"
    )
    return DiagramModuleArtifact(
        diagram_id=semantics.diagram_id.replace("_semantics", "_modules"),
        route_id=semantics.route_id,
        module_kind=DiagramLevel.PID_LITE,
        modules=modules,
        citations=semantics.citations,
        assumptions=semantics.assumptions + ["P&ID-lite modules isolate one local equipment cluster per sheet-ready module."],
        markdown=markdown,
    )


def build_pid_lite_sheet_composition(
    modules: DiagramModuleArtifact,
    style: DiagramStyleProfile,
) -> DiagramSheetCompositionArtifact:
    sheets: list[DiagramSheetComposition] = []
    bac_pid_mode = any("BAC " in module.title for module in modules.modules)
    for sheet_index, module in enumerate(modules.modules, start=1):
        width_px = max(style.canvas_width_px, 1100 if bac_pid_mode else 1180)
        height_px = max(style.canvas_height_px, 800 if bac_pid_mode else 860)
        sheets.append(
            DiagramSheetComposition(
                sheet_id=f"sheet_{sheet_index}",
                title=module.title,
                diagram_level=DiagramLevel.PID_LITE,
                width_px=width_px,
                height_px=height_px,
                module_placements=[
                    DiagramModulePlacement(
                        module_id=module.module_id,
                        sheet_id=f"sheet_{sheet_index}",
                        x=86.0 if bac_pid_mode else 110.0,
                        y=116.0 if bac_pid_mode else 130.0,
                        width=width_px - (172.0 if bac_pid_mode else 220.0),
                        height=height_px - (206.0 if bac_pid_mode else 240.0),
                        z_index=1,
                    )
                ],
                connectors=[],
                legend_mode="embedded",
                title_block_mode="embedded",
            )
        )
    if bac_pid_mode:
        _apply_bac_pid_stitching_metadata(sheets)
    markdown = (
        "### P&ID-lite Sheet Composition\n\n"
        f"- Sheets: {len(sheets)}\n"
        "- Each isolated unit cluster is placed on its own readable sheet.\n"
    )
    if bac_pid_mode:
        markdown += "- BAC stitched panels preserve local unit isolation while adding continuation references between related sheets.\n"
    return DiagramSheetCompositionArtifact(
        diagram_id=modules.diagram_id.replace("_modules", "_sheet_composition"),
        route_id=modules.route_id,
        diagram_level=DiagramLevel.PID_LITE,
        sheets=sheets,
        citations=modules.citations,
        assumptions=modules.assumptions + ["P&ID-lite sheets keep local unit clusters isolated instead of mixing them into the PFD body."],
        markdown=markdown,
    )


def build_pid_lite_diagram(
    flowsheet_graph: FlowsheetGraph,
    stream_table: StreamTable,
    control_plan: ControlPlanArtifact,
    style: DiagramStyleProfile,
    semantics: PlantDiagramSemanticsArtifact | None = None,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
    routing: DiagramRoutingArtifact | None = None,
    target: DiagramTargetProfile | None = None,
) -> PidLiteDiagramArtifact:
    if semantics is None or modules is None or sheet_composition is None:
        symbol_library = build_diagram_symbol_library()
        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, symbol_library, target)
        modules = build_pid_lite_modules(semantics, symbol_library)
        sheet_composition = build_pid_lite_sheet_composition(modules, style)

    entity_lookup = {entity.entity_id: entity for entity in semantics.entities}
    node_family_map = {
        "pid_indicator": "instrument",
        "pid_transmitter": "instrument",
        "pid_controller": "controller",
        "pid_manual_valve": "valve",
        "pid_control_valve": "valve",
        "pid_relief_valve": "relief_valve",
    }
    node_templates: dict[str, DiagramNode] = {}
    bac_pid_mode = target is not None and _is_bac_target(target)
    if not bac_pid_mode:
        bac_pid_mode = any(entity.metadata.get("bac_pid_profile", "") == "true" for entity in semantics.entities)
    for rank, entity in enumerate(semantics.entities):
        primary_text = entity.instrument_id or entity.equipment_tag or entity.unit_id or entity.label
        secondary_text = entity.pid_function.replace("_", " ").title() if entity.pid_function else entity.service
        labels = [DiagramLabel(text=primary_text, kind="primary")]
        if secondary_text and secondary_text != primary_text:
            labels.append(DiagramLabel(text=secondary_text, kind="secondary"))
        if entity.pid_loop_id:
            labels.append(DiagramLabel(text=entity.pid_loop_id, kind="utility"))
        note_parts = [entity.symbol_key]
        if entity.attachment_role:
            note_parts.append(f"attachment_role={entity.attachment_role}")
        template_id = entity.metadata.get("template_id", "")
        template_family = entity.metadata.get("template_family", "")
        if template_id:
            note_parts.append(f"template_id={template_id}")
        if template_family:
            note_parts.append(f"template_family={template_family}")
        node_family = node_family_map.get(entity.symbol_key, "vessel")
        if entity.symbol_key == "pid_unit":
            node_family = _template_family_to_node_family(entity.metadata.get("template_family", "vessel"))
        node_templates[entity.entity_id] = DiagramNode(
            node_id=entity.entity_id,
            label=entity.label,
            node_family=node_family,
            section_id=entity.section_id,
            equipment_tag=primary_text,
            labels=labels,
            layout=DiagramLayoutHints(rank=rank),
            notes=";".join(note_parts),
        )
    connection_lookup = {connection.connection_id: connection for connection in semantics.connections}
    nodes: list[DiagramNode] = []
    sheets: list[DiagramSheet] = []
    module_lookup = {module.module_id: module for module in modules.modules}
    composition_lookup = {sheet.sheet_id: sheet for sheet in sheet_composition.sheets}
    edges: list[DiagramEdge] = []

    for sheet in sheet_composition.sheets:
        placement = sheet.module_placements[0] if sheet.module_placements else None
        if placement is None:
            continue
        module = module_lookup.get(placement.module_id)
        if module is None:
            continue
        sheet_nodes: list[DiagramNode] = []
        sheet_entity_lookup: dict[str, PlantDiagramEntity] = {}
        node_id_map: dict[str, str] = {}
        for entity_id in module.entity_ids:
            template = node_templates.get(entity_id)
            entity = entity_lookup.get(entity_id)
            if template is None or entity is None:
                continue
            clone_id = f"{sheet.sheet_id}__{entity_id}"
            cloned_node = template.model_copy(deep=True)
            cloned_node.node_id = clone_id
            sheet_nodes.append(cloned_node)
            nodes.append(cloned_node)
            node_id_map[entity_id] = clone_id
            sheet_entity_lookup[clone_id] = entity

        _layout_pid_lite_module_nodes(sheet_nodes, placement, sheet_entity_lookup)

        sheet_edges: list[DiagramEdge] = []
        for connection_id in module.connection_ids:
            connection = connection_lookup.get(connection_id)
            if connection is None:
                continue
            source_clone_id = node_id_map.get(connection.source_entity_id)
            target_clone_id = node_id_map.get(connection.target_entity_id)
            if not source_clone_id or not target_clone_id:
                continue
            edge_type = {
                DiagramEdgeRole.PROCESS: "main",
                DiagramEdgeRole.PRODUCT: "product",
                DiagramEdgeRole.UTILITY: "utility",
                DiagramEdgeRole.CONTROL_SIGNAL: "control_signal",
                DiagramEdgeRole.SAFEGUARD: "safeguard",
                DiagramEdgeRole.CONTINUATION: "continuation",
            }.get(connection.role, "main")
            sheet_edges.append(
                DiagramEdge(
                    edge_id=f"{sheet.sheet_id}__{connection.connection_id}",
                    source_node_id=source_clone_id,
                    target_node_id=target_clone_id,
                    edge_type=edge_type,
                    stream_id=connection.stream_id,
                    label=connection.label,
                    condition_label=_display_pid_line_class(connection.line_class, bac_pid_mode=bac_pid_mode) if connection.line_class else "",
                    sheet_id=sheet.sheet_id,
                    notes=f"lane={connection.preferred_lane}",
                )
            )
        edges.extend(sheet_edges)

        rendered_sheet = DiagramSheet(
            sheet_id=sheet.sheet_id,
            title=sheet.title,
            width_px=sheet.width_px,
            height_px=sheet.height_px,
            stitch_panel_id=sheet.stitch_panel_id,
            stitch_panel_title=sheet.stitch_panel_title,
            stitch_prev_sheet_id=sheet.stitch_prev_sheet_id,
            stitch_next_sheet_id=sheet.stitch_next_sheet_id,
            orientation="landscape",
            presentation_mode="sheet",
            preferred_scale=1.0,
            full_page=True,
            legend_mode="embedded",
            suppress_inline_wrapping=True,
            node_ids=[node.node_id for node in sheet_nodes],
            edge_ids=[edge.edge_id for edge in sheet_edges],
        )
        composition_sheet = composition_lookup.get(sheet.sheet_id)
        module_placements = composition_sheet.module_placements if composition_sheet is not None else []
        module_titles = {
            placement.module_id: module_lookup[placement.module_id].title
            for placement in module_placements
            if placement.module_id in module_lookup
        }
        if routing is not None:
            routing_sheet = next((item for item in routing.sheets if item.sheet_id == sheet.sheet_id), None)
            route_hints = {
                hint.edge_id: {
                    "points": [(point.x, point.y) for point in hint.points],
                    "label": (hint.label_x, hint.label_y),
                    "condition": (hint.condition_x, hint.condition_y),
                }
                for hint in (routing_sheet.route_hints if routing_sheet is not None else [])
            }
            continuation_markers: list[dict[str, object]] = []
        else:
            route_hints = _build_pid_lite_route_hints(sheet.sheet_id, sheet_edges, sheet_nodes, sheet_entity_lookup)
            continuation_markers = _build_pid_sheet_continuation_markers(sheet.sheet_id, semantics, modules, sheet_composition)
        apply_diagram_drafting_metadata([rendered_sheet], drawing_prefix=f"{flowsheet_graph.route_id}-PID")
        rendered_sheet.svg = _render_svg(
            rendered_sheet,
            sheet_nodes,
            sheet_edges,
            style,
            subtitle=(sheet.stitch_panel_title or "Isolated local instrumentation, control, and valve cluster"),
            module_placements=module_placements,
            module_titles=module_titles,
            continuation_markers=continuation_markers,
            route_hints=route_hints,
        )
        sheets.append(rendered_sheet)

    markdown = (
        "### Diagram Basis\n\n"
        "The P&ID-lite sheets below isolate local unit clusters with their principal transmitters, indicators, controllers, control valves, and safeguards.\n"
    )
    return PidLiteDiagramArtifact(
        diagram_id=f"{flowsheet_graph.route_id}_pid_lite",
        route_id=flowsheet_graph.route_id,
        nodes=nodes,
        edges=edges,
        sheets=sheets,
        citations=sorted(set(flowsheet_graph.citations + stream_table.citations + control_plan.citations)),
        assumptions=flowsheet_graph.assumptions
        + stream_table.assumptions
        + control_plan.assumptions
        + [
            "P&ID-lite diagrams isolate one local equipment cluster per sheet rather than replacing the report-grade PFD.",
            "The renderer shows simplified valve and instrument topology without claiming full drafting-grade ISA detail.",
        ],
        markdown=markdown,
    )


def build_pid_lite_routing_artifact(
    semantics: PlantDiagramSemanticsArtifact,
    modules: DiagramModuleArtifact,
    sheet_composition: DiagramSheetCompositionArtifact,
    diagram: PidLiteDiagramArtifact,
) -> DiagramRoutingArtifact:
    node_lookup = {node.node_id: node for node in diagram.nodes}
    entity_lookup = {
        node.node_id: semantics_entity
        for node in diagram.nodes
        for semantics_entity in [next((entity for entity in semantics.entities if node.node_id.endswith(f"__{entity.entity_id}")), None)]
        if semantics_entity is not None
    }
    routing_sheets: list[DiagramRoutingSheet] = []
    for sheet in diagram.sheets:
        sheet_nodes = [node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup]
        sheet_edges = [edge for edge in diagram.edges if edge.sheet_id == sheet.sheet_id]
        sheet_entity_lookup = {node.node_id: entity_lookup[node.node_id] for node in sheet_nodes if node.node_id in entity_lookup}
        route_hints = _build_pid_lite_route_hints(sheet.sheet_id, sheet_edges, sheet_nodes, sheet_entity_lookup)
        crossing_count, congested_connector_count, max_channel_load = _routing_quality_metrics(route_hints)
        routing_sheets.append(
            DiagramRoutingSheet(
                sheet_id=sheet.sheet_id,
                route_hints=[
                    DiagramRouteHint(
                        edge_id=edge_id,
                        points=[DiagramRoutePoint(x=point[0], y=point[1]) for point in hint.get("points", [])],
                        label_x=float(hint.get("label", (0.0, 0.0))[0]),
                        label_y=float(hint.get("label", (0.0, 0.0))[1]),
                        condition_x=float(hint.get("condition", (0.0, 0.0))[0]),
                        condition_y=float(hint.get("condition", (0.0, 0.0))[1]),
                    )
                    for edge_id, hint in route_hints.items()
                ],
                continuation_markers=[],
                crossing_count=crossing_count,
                congested_connector_count=congested_connector_count,
                max_channel_load=max_channel_load,
            )
        )
    markdown = (
        "### Routing Stage\n\n"
        f"- Routing sheets: {len(routing_sheets)}\n"
        f"- Route hints: {sum(len(item.route_hints) for item in routing_sheets)}\n"
        f"- Route crossings: {sum(item.crossing_count for item in routing_sheets)}\n"
        f"- Congested connectors: {sum(item.congested_connector_count for item in routing_sheets)}\n"
    )
    return DiagramRoutingArtifact(
        diagram_id=f"{diagram.diagram_id}_routing",
        route_id=diagram.route_id,
        diagram_level=DiagramLevel.PID_LITE,
        sheets=routing_sheets,
        citations=diagram.citations,
        assumptions=diagram.assumptions + ["P&ID-lite route geometry is persisted as a distinct routing stage artifact before final rendering."],
        markdown=markdown,
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
        display_label = _display_bfd_section(section_key, target=target)
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
        register_section(required, _display_bfd_section(required, target=target))

    if _is_bac_target(target):
        section_order = _ordered_bfd_sections(section_index.keys(), target)
        section_nodes.sort(key=lambda node: section_order.index(node.section_id) if node.section_id in section_order else len(section_order))
        section_transition_pairs = list(zip(section_order, section_order[1:]))

    if _is_bac_target(target):
        _layout_bac_bfd_nodes(section_nodes, style)
    else:
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

    if _is_bac_target(target):
        dynamic_width = int(max((node.x + node.width) for node in section_nodes) + 150)
        dynamic_height = int(max((node.y + node.height) for node in section_nodes) + 140)
    else:
        dynamic_width = max(style.canvas_width_px, int(max((node.x + node.width) for node in section_nodes) + 80))
        dynamic_height = max(style.canvas_height_px, int(max((node.y + node.height) for node in section_nodes) + 160))
    sheet = DiagramSheet(
        sheet_id="sheet_1",
        title="Block Flow Diagram",
        width_px=dynamic_width,
        height_px=dynamic_height if _is_bac_target(target) else max(style.canvas_height_px, 820),
        orientation="portrait" if _is_bac_target(target) else "landscape",
        presentation_mode="sheet",
        preferred_scale=1.0,
        full_page=True,
        legend_mode="suppressed",
        suppress_inline_wrapping=True,
        node_ids=[node.node_id for node in section_nodes],
        edge_ids=[edge.edge_id for edge in edges],
    )
    apply_diagram_drafting_metadata([sheet], drawing_prefix=f"{blueprint.route_id}-BFD")
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
    semantics: PlantDiagramSemanticsArtifact | None = None,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
    routing: DiagramRoutingArtifact | None = None,
) -> ProcessFlowDiagramArtifact:
    if semantics is None or modules is None or sheet_composition is None:
        symbol_library = build_diagram_symbol_library()
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, symbol_library)
        modules = build_process_flow_diagram_modules(semantics, symbol_library)
        sheet_composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)

    equipment_index = {item.equipment_id: item for item in (equipment.items if equipment is not None else [])}
    equipment_items = equipment.items if equipment is not None else []
    stream_index = {stream.stream_id: stream for stream in stream_table.streams}
    semantic_entity_by_unit = {
        entity.unit_id: entity for entity in (semantics.entities if semantics is not None else []) if entity.unit_id
    }
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
    suppress_auxiliary_pfd_labels = _is_bac_target(target)
    for rank, node in enumerate(flowsheet_graph.nodes):
        semantic_entity = semantic_entity_by_unit.get(node.node_id)
        equipment_tag, display_label, node_family, equipment_item = _resolve_pfd_identity(
            node,
            equipment_items,
            target,
        )
        labels = [DiagramLabel(text=equipment_tag, kind="primary")]
        labels.append(DiagramLabel(text=display_label, kind="secondary"))
        loop_ids = _control_loop_ids_for_node(node, equipment_item.equipment_id if equipment_item is not None else "", loops_by_unit)
        if loop_ids and not suppress_auxiliary_pfd_labels:
            labels.append(DiagramLabel(text=", ".join(loop_ids[:2]), kind="utility"))
        if utility_note_by_unit.get(node.node_id) and not suppress_auxiliary_pfd_labels:
            labels.append(DiagramLabel(text=utility_note_by_unit[node.node_id], kind="utility"))
        notes = node.notes
        if suppress_auxiliary_pfd_labels and loop_ids:
            notes = _append_note_value(notes, "suppressed_loop_ids", ",".join(loop_ids[:3]))
        if suppress_auxiliary_pfd_labels and utility_note_by_unit.get(node.node_id):
            notes = _append_note_value(notes, "suppressed_utility_note", utility_note_by_unit[node.node_id])
        if semantic_entity is not None:
            template_id = semantic_entity.metadata.get("template_id", "")
            template_family = semantic_entity.metadata.get("template_family", "")
            if template_id:
                notes = _append_note_value(notes, "template_id", template_id)
            if template_family:
                notes = _append_note_value(notes, "template_family", template_family)
        nodes.append(
            DiagramNode(
                node_id=node.node_id,
                label=node.label,
                node_family=node_family,
                section_id=node.section_id,
                equipment_tag=equipment_tag,
                labels=labels,
                layout=DiagramLayoutHints(rank=rank),
                notes=notes,
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

    sheets = _build_pfd_sheets_from_composition(nodes, modules, sheet_composition, style, target)
    node_lookup = {node.node_id: node for node in nodes}

    edges = _build_pfd_edges_from_semantics(
        semantics,
        modules,
        sheet_composition,
        stream_index,
        sheets,
        target,
    )

    sheet_lookup = {sheet.sheet_id: sheet for sheet in sheets}
    module_lookup = {module.module_id: module for module in modules.modules} if modules is not None else {}
    for edge in edges:
        sheet_lookup[edge.sheet_id].edge_ids.append(edge.edge_id)
    apply_diagram_drafting_metadata(sheets, drawing_prefix=f"{flowsheet_graph.route_id}-PFD")
    for sheet in sheets:
        sheet_nodes = [node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup]
        sheet_edges = [edge for edge in edges if edge.sheet_id == sheet.sheet_id]
        composition_sheet = next((item for item in sheet_composition.sheets if item.sheet_id == sheet.sheet_id), None) if sheet_composition is not None else None
        module_placements = composition_sheet.module_placements if composition_sheet is not None else []
        module_titles = {placement.module_id: module_lookup[placement.module_id].title for placement in module_placements if placement.module_id in module_lookup}
        if routing is not None:
            routing_sheet = next((item for item in routing.sheets if item.sheet_id == sheet.sheet_id), None)
            continuation_markers = [
                {
                    "x": marker.x,
                    "y": marker.y,
                    "side": marker.side,
                    "label": marker.label,
                    "target_sheet": marker.target_sheet,
                }
                for marker in (routing_sheet.continuation_markers if routing_sheet is not None else [])
            ]
            route_hints = {
                hint.edge_id: {
                    "points": [(point.x, point.y) for point in hint.points],
                    "label": (hint.label_x, hint.label_y),
                    "condition": (hint.condition_x, hint.condition_y),
                }
                for hint in (routing_sheet.route_hints if routing_sheet is not None else [])
            }
        else:
            continuation_markers = _build_pfd_sheet_continuation_markers(sheet.sheet_id, semantics, modules, sheet_composition) if semantics is not None and modules is not None and sheet_composition is not None else []
            route_hints = _build_pfd_sheet_route_hints(sheet.sheet_id, sheet_edges, sheet_nodes, modules, sheet_composition, target) if modules is not None and sheet_composition is not None else {}
        sheet.svg = _render_svg(
            sheet,
            sheet_nodes,
            sheet_edges,
            style,
            subtitle="Equipment-level process flow representation",
            module_placements=module_placements,
            module_titles=module_titles,
            continuation_markers=continuation_markers,
            route_hints=route_hints,
        )

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


def build_process_flow_diagram_routing_artifact(
    semantics: PlantDiagramSemanticsArtifact,
    modules: DiagramModuleArtifact,
    sheet_composition: DiagramSheetCompositionArtifact,
    diagram: ProcessFlowDiagramArtifact,
    target: DiagramTargetProfile | None = None,
) -> DiagramRoutingArtifact:
    node_lookup = {node.node_id: node for node in diagram.nodes}
    routing_sheets: list[DiagramRoutingSheet] = []
    for sheet in diagram.sheets:
        sheet_nodes = [node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup]
        sheet_edges = [edge for edge in diagram.edges if edge.sheet_id == sheet.sheet_id]
        route_hints = _build_pfd_sheet_route_hints(sheet.sheet_id, sheet_edges, sheet_nodes, modules, sheet_composition, target)
        continuation_markers = _build_pfd_sheet_continuation_markers(sheet.sheet_id, semantics, modules, sheet_composition)
        crossing_count, congested_connector_count, max_channel_load = _routing_quality_metrics(route_hints)
        routing_sheets.append(
            DiagramRoutingSheet(
                sheet_id=sheet.sheet_id,
                route_hints=[
                    DiagramRouteHint(
                        edge_id=edge_id,
                        points=[DiagramRoutePoint(x=point[0], y=point[1]) for point in hint.get("points", [])],
                        label_x=float(hint.get("label", (0.0, 0.0))[0]),
                        label_y=float(hint.get("label", (0.0, 0.0))[1]),
                        condition_x=float(hint.get("condition", (0.0, 0.0))[0]),
                        condition_y=float(hint.get("condition", (0.0, 0.0))[1]),
                    )
                    for edge_id, hint in route_hints.items()
                ],
                continuation_markers=[
                    DiagramContinuationMarker(
                        x=float(marker.get("x", 0.0)),
                        y=float(marker.get("y", 0.0)),
                        side=str(marker.get("side", "right")),
                        label=str(marker.get("label", "")),
                        target_sheet=str(marker.get("target_sheet", "")),
                    )
                    for marker in continuation_markers
                ],
                crossing_count=crossing_count,
                congested_connector_count=congested_connector_count,
                max_channel_load=max_channel_load,
            )
        )
    markdown = (
        "### Routing Stage\n\n"
        f"- Routing sheets: {len(routing_sheets)}\n"
        f"- Route hints: {sum(len(item.route_hints) for item in routing_sheets)}\n"
        f"- Continuation markers: {sum(len(item.continuation_markers) for item in routing_sheets)}\n"
        f"- Route crossings: {sum(item.crossing_count for item in routing_sheets)}\n"
        f"- Congested connectors: {sum(item.congested_connector_count for item in routing_sheets)}\n"
    )
    return DiagramRoutingArtifact(
        diagram_id=f"{diagram.diagram_id}_routing",
        route_id=diagram.route_id,
        diagram_level=DiagramLevel.PFD,
        sheets=routing_sheets,
        citations=diagram.citations,
        assumptions=diagram.assumptions + ["PFD route geometry is persisted as a distinct routing stage artifact before final rendering."],
        markdown=markdown,
    )


def _routing_quality_metrics(route_hints: dict[str, dict[str, object]]) -> tuple[int, int, int]:
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    channel_loads: dict[tuple[str, int], int] = {}
    for hint in route_hints.values():
        points = [(float(point[0]), float(point[1])) for point in hint.get("points", [])]
        for left, right in zip(points, points[1:]):
            if left == right:
                continue
            segments.append((left, right))
            if abs(left[0] - right[0]) < 0.1:
                key = ("v", int(round(left[0])))
            elif abs(left[1] - right[1]) < 0.1:
                key = ("h", int(round(left[1])))
            else:
                continue
            channel_loads[key] = channel_loads.get(key, 0) + 1
    crossing_count = 0
    for index, first in enumerate(segments):
        for second in segments[index + 1 :]:
            if _orthogonal_segments_cross(first, second):
                crossing_count += 1
    congested_connector_count = sum(1 for load in channel_loads.values() if load >= 4)
    max_channel_load = max(channel_loads.values(), default=0)
    return crossing_count, congested_connector_count, max_channel_load


def _orthogonal_segments_cross(
    first: tuple[tuple[float, float], tuple[float, float]],
    second: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    (x1, y1), (x2, y2) = first
    (x3, y3), (x4, y4) = second
    first_vertical = abs(x1 - x2) < 0.1
    second_vertical = abs(x3 - x4) < 0.1
    if first_vertical == second_vertical:
        return False
    if first_vertical:
        vx, vy1, vy2 = x1, min(y1, y2), max(y1, y2)
        hy, hx1, hx2 = y3, min(x3, x4), max(x3, x4)
    else:
        vx, vy1, vy2 = x3, min(y3, y4), max(y3, y4)
        hy, hx1, hx2 = y1, min(x1, x2), max(x1, x2)
    return hx1 < vx < hx2 and vy1 < hy < vy2


def build_control_system_diagram(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    flowsheet_graph: FlowsheetGraph,
    style: DiagramStyleProfile,
    flowsheet_case: FlowsheetCase | None = None,
    semantics: PlantDiagramSemanticsArtifact | None = None,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
    routing: DiagramRoutingArtifact | None = None,
) -> ControlSystemDiagramArtifact:
    if semantics is None or modules is None or sheet_composition is None:
        symbol_library = build_diagram_symbol_library()
        semantics = build_control_system_semantics(control_plan, control_architecture, flowsheet_graph, symbol_library)
        modules = build_control_system_modules(semantics, symbol_library)
        sheet_composition = build_control_system_sheet_composition(modules, style)
    loop_groups: dict[str, list] = {}
    unit_label_by_id = {node.node_id: node.label for node in flowsheet_graph.nodes}
    for loop in control_plan.control_loops:
        unit_id = loop.unit_id or "plant_supervisory"
        loop_groups.setdefault(unit_id, []).append(loop)

    ordered_unit_ids = _ordered_control_units_from_composition(modules, sheet_composition)
    ordered_unit_ids = [unit_id for unit_id in ordered_unit_ids if unit_id in loop_groups]
    ordered_unit_ids.extend(unit_id for unit_id in control_architecture.critical_units if unit_id in loop_groups and unit_id not in ordered_unit_ids)
    ordered_unit_ids.extend(unit_id for unit_id in loop_groups if unit_id not in ordered_unit_ids)
    ordered_unit_ids = ordered_unit_ids[:6]
    architecture_sheet = next((sheet for sheet in sheet_composition.sheets if sheet.sheet_id == "sheet_1"), None)
    width_px = architecture_sheet.width_px if architecture_sheet is not None else max(1700, 250 * max(4, len(ordered_unit_ids)) + 220)
    height_px = architecture_sheet.height_px if architecture_sheet is not None else 980
    architecture_module_placements = architecture_sheet.module_placements if architecture_sheet is not None else []
    architecture_module_titles = {
        placement.module_id: next((module.title for module in modules.modules if module.module_id == placement.module_id), placement.module_id)
        for placement in architecture_module_placements
    }
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
        module_placements=architecture_module_placements,
        module_titles=architecture_module_titles,
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
    overlay_sheet = _build_instrumented_overlay_sheet(
        control_plan,
        control_architecture,
        style,
        modules=modules,
        sheet_composition=sheet_composition,
        routing=routing,
    )
    sheets.append(overlay_sheet)
    interlock_sheet = _build_control_interlock_sheet(
        control_plan,
        flowsheet_graph,
        style,
        modules=modules,
        sheet_composition=sheet_composition,
    )
    sheets.append(interlock_sheet)
    shutdown_sheet = _build_control_shutdown_sheet(
        control_plan,
        flowsheet_graph,
        style,
        modules=modules,
        sheet_composition=sheet_composition,
    )
    sheets.append(shutdown_sheet)
    apply_diagram_drafting_metadata(sheets, drawing_prefix=f"{flowsheet_graph.route_id}-CTRL")
    markdown = (
        "### Diagram Basis\n\n"
        "The control-system diagrams below show the major controlled units, the principal loop clusters, their supervisory control architecture, and the main interlock/permissive logic summaries.\n"
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
            "The interlock and permissive sheet summarizes startup, shutdown, override, and safeguard logic for the principal loop clusters.",
            "The shutdown and protective trip sheet isolates safety-critical actions for focused review.",
        ],
        markdown=markdown,
    )


def build_control_system_routing_artifact(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    flowsheet_graph: FlowsheetGraph,
    style: DiagramStyleProfile,
    modules: DiagramModuleArtifact,
    sheet_composition: DiagramSheetCompositionArtifact,
    diagram: ControlSystemDiagramArtifact,
) -> DiagramRoutingArtifact:
    overlay_sheet = next((sheet for sheet in diagram.sheets if sheet.sheet_id == "sheet_2"), None)
    if overlay_sheet is None:
        return DiagramRoutingArtifact(
            diagram_id=f"{diagram.diagram_id}_routing",
            route_id=diagram.route_id,
            diagram_level=DiagramLevel.CONTROL,
            sheets=[],
            citations=diagram.citations,
            assumptions=diagram.assumptions + ["Control routing artifact omitted because no instrumented overlay sheet was present."],
            markdown="### Routing Stage\n\n- Routing sheets: 0\n",
        )
    overlay_nodes, overlay_edges = _build_control_overlay_nodes_and_edges(
        control_plan,
        control_architecture,
        style,
        modules=modules,
        sheet_composition=sheet_composition,
    )
    route_hints = _build_control_overlay_route_hints(overlay_edges, overlay_nodes)
    crossing_count, congested_connector_count, max_channel_load = _routing_quality_metrics(route_hints)
    routing_sheet = DiagramRoutingSheet(
        sheet_id="sheet_2",
        route_hints=[
            DiagramRouteHint(
                edge_id=edge_id,
                points=[DiagramRoutePoint(x=point[0], y=point[1]) for point in hint.get("points", [])],
                label_x=float(hint.get("label", (0.0, 0.0))[0]),
                label_y=float(hint.get("label", (0.0, 0.0))[1]),
                condition_x=float(hint.get("condition", (0.0, 0.0))[0]),
                condition_y=float(hint.get("condition", (0.0, 0.0))[1]),
            )
            for edge_id, hint in route_hints.items()
        ],
        continuation_markers=[],
        crossing_count=crossing_count,
        congested_connector_count=congested_connector_count,
        max_channel_load=max_channel_load,
    )
    markdown = (
        "### Routing Stage\n\n"
        "- Routing sheets: 1\n"
        f"- Route hints: {len(routing_sheet.route_hints)}\n"
        f"- Route crossings: {routing_sheet.crossing_count}\n"
        f"- Congested connectors: {routing_sheet.congested_connector_count}\n"
    )
    return DiagramRoutingArtifact(
        diagram_id=f"{diagram.diagram_id}_routing",
        route_id=diagram.route_id,
        diagram_level=DiagramLevel.CONTROL,
        sheets=[routing_sheet],
        citations=diagram.citations,
        assumptions=diagram.assumptions + ["Control overlay route geometry is persisted as a distinct routing stage artifact before final rendering."],
        markdown=markdown,
    )


def build_control_cause_effect_artifact(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    flowsheet_graph: FlowsheetGraph,
) -> ControlCauseEffectArtifact:
    rows: list[ControlCauseEffectRow] = []
    for loop in control_plan.control_loops:
        rows.append(
            ControlCauseEffectRow(
                control_id=loop.control_id,
                unit_id=loop.unit_id or "",
                controlled_variable=loop.controlled_variable,
                cause_permissive=loop.startup_logic or "Standard startup permissive",
                action_shutdown=loop.shutdown_logic or "Standard shutdown rundown",
                override_logic=loop.override_logic or "Basic operator override",
                safeguard_trip=loop.safeguard_linkage or "No dedicated trip linkage",
                protected_final_action=loop.manipulated_variable or loop.actuator or "Protective action",
                criticality=loop.criticality or "medium",
                safety_critical=bool(loop.safeguard_linkage or (loop.criticality or "").lower() == "high"),
                citations=loop.citations,
                assumptions=loop.assumptions,
            )
        )
    markdown = (
        "### Control Cause and Effect\n\n"
        f"- Review rows: {len(rows)}\n"
        f"- Safety-critical rows: {sum(1 for row in rows if row.safety_critical)}\n"
    )
    return ControlCauseEffectArtifact(
        artifact_id=f"{flowsheet_graph.route_id}_control_cause_effect",
        route_id=flowsheet_graph.route_id,
        rows=rows,
        citations=sorted(set(control_plan.citations + control_architecture.citations + flowsheet_graph.citations)),
        assumptions=control_plan.assumptions + control_architecture.assumptions + flowsheet_graph.assumptions + ["Cause/effect rows consolidate permissive, shutdown, override, and safeguard logic for control review exports."],
        markdown=markdown,
    )


def build_diagram_acceptance(
    *,
    diagram_kind: str,
    diagram_id: str,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    target: DiagramTargetProfile,
    sheets: list[DiagramSheet] | None = None,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
    routing: DiagramRoutingArtifact | None = None,
    blueprint: FlowsheetBlueprintArtifact | None = None,
    flowsheet_graph: FlowsheetGraph | None = None,
    flowsheet_case: FlowsheetCase | None = None,
) -> DiagramAcceptanceArtifact:
    missing_nodes: list[str] = []
    missing_edges: list[str] = []
    mismatched_labels: list[str] = []
    notes: list[str] = []
    warning_issue_codes: list[str] = []
    blocking_issue_codes: list[str] = []
    benchmark_cleanliness_score = 1.0
    node_overlap_count = 0
    node_label_overlap_count = 0
    crowded_sheet_count = 0
    max_sheet_utilization_fraction = 0.0
    missing_drafting_field_count = 0
    duplicate_drawing_number_count = 0
    duplicate_sheet_number_count = 0
    missing_title_block_count = 0
    title_block_overlap_count = 0
    route_crossings = 0
    route_congestion = 0
    max_channel_load = 0
    node_labels = [node.label.lower() for node in nodes]
    edge_types = {edge.edge_type for edge in edges}
    bac_pfd_mode = diagram_kind != "bfd" and _is_bac_target(target)

    if diagram_kind == "bfd":
        for required in target.required_bfd_sections:
            if not any(required in label or required in node.section_id.lower() for node, label in zip(nodes, node_labels)):
                missing_nodes.append(required)
        if blueprint is not None and blueprint.recycle_intents and "recycle" not in edge_types:
            missing_edges.append("recycle path")
        if sheets is not None:
            (
                missing_drafting_field_count,
                duplicate_drawing_number_count,
                duplicate_sheet_number_count,
                missing_title_block_count,
                title_block_overlap_count,
            ) = _diagram_drafting_quality_metrics(sheets, nodes)
            if missing_drafting_field_count:
                notes.append(f"Drafting QA: {missing_drafting_field_count} required drafting metadata fields are missing.")
            if duplicate_drawing_number_count:
                notes.append(f"Drafting QA: {duplicate_drawing_number_count} duplicate drawing numbers detected.")
            if duplicate_sheet_number_count:
                notes.append(f"Drafting QA: {duplicate_sheet_number_count} duplicate sheet numbers detected.")
            if missing_title_block_count:
                notes.append(f"Drafting QA: {missing_title_block_count} rendered sheets are missing the drafting title block.")
            if title_block_overlap_count:
                notes.append(f"Drafting QA: {title_block_overlap_count} equipment boxes overlap the title-block reserved area.")
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
        if sheets is not None:
            (
                node_overlap_count,
                node_label_overlap_count,
                crowded_sheet_count,
                max_sheet_utilization_fraction,
                benchmark_cleanliness_score,
            ) = _diagram_cleanliness_metrics(nodes, sheets, modules=modules, sheet_composition=sheet_composition)
            (
                missing_drafting_field_count,
                duplicate_drawing_number_count,
                duplicate_sheet_number_count,
                missing_title_block_count,
                title_block_overlap_count,
            ) = _diagram_drafting_quality_metrics(sheets, nodes)
            if node_overlap_count:
                notes.append(f"PFD layout benchmark: {node_overlap_count} node overlaps detected.")
            if node_label_overlap_count:
                notes.append(f"PFD layout benchmark: {node_label_overlap_count} node-label overlaps detected.")
            if crowded_sheet_count:
                notes.append(f"PFD layout benchmark: {crowded_sheet_count} crowded sheets exceed the readability threshold.")
            if max_sheet_utilization_fraction > 0.86:
                notes.append(f"PFD layout benchmark: max sheet utilization reached {max_sheet_utilization_fraction:.0%}.")
            if missing_drafting_field_count:
                notes.append(f"Drafting QA: {missing_drafting_field_count} required drafting metadata fields are missing.")
            if duplicate_drawing_number_count:
                notes.append(f"Drafting QA: {duplicate_drawing_number_count} duplicate drawing numbers detected.")
            if duplicate_sheet_number_count:
                notes.append(f"Drafting QA: {duplicate_sheet_number_count} duplicate sheet numbers detected.")
            if missing_title_block_count:
                notes.append(f"Drafting QA: {missing_title_block_count} rendered sheets are missing the drafting title block.")
            if title_block_overlap_count:
                notes.append(f"Drafting QA: {title_block_overlap_count} equipment boxes overlap the title-block reserved area.")
        if routing is not None:
            route_crossings = sum(sheet.crossing_count for sheet in routing.sheets)
            route_congestion = sum(sheet.congested_connector_count for sheet in routing.sheets)
            max_channel_load = max((sheet.max_channel_load for sheet in routing.sheets), default=0)
            if route_crossings:
                notes.append(f"PFD routing benchmark: {route_crossings} orthogonal crossings detected.")
            if route_congestion:
                notes.append(f"PFD routing benchmark: {route_congestion} congested routing channels detected.")
            if max_channel_load >= 4:
                notes.append(f"PFD routing benchmark: max routing channel load reached {max_channel_load}.")
            benchmark_cleanliness_score = max(
                0.0,
                benchmark_cleanliness_score - route_crossings * 0.015 - route_congestion * 0.03 - max(0, max_channel_load - 3) * 0.02,
            )
        if not missing_nodes and not missing_edges and not mismatched_labels:
            notes.append("PFD contains the major units and stream roles expected from the solved flowsheet.")

    overall_status = "complete"
    if missing_nodes:
        warning_issue_codes.append("diagram_missing_required_nodes")
    if missing_edges:
        warning_issue_codes.append("diagram_missing_required_edges")
    if mismatched_labels:
        warning_issue_codes.append("diagram_label_mismatch")
    if crowded_sheet_count:
        warning_issue_codes.append("diagram_crowded_sheet")
    if benchmark_cleanliness_score < 0.78:
        warning_issue_codes.append("diagram_cleanliness_below_target")
    if routing is not None and sum(sheet.congested_connector_count for sheet in routing.sheets):
        warning_issue_codes.append("diagram_route_congestion")
    if routing is not None and sum(sheet.crossing_count for sheet in routing.sheets) >= 4:
        warning_issue_codes.append("diagram_route_crossings")
    if max_sheet_utilization_fraction > 0.86:
        warning_issue_codes.append("diagram_high_sheet_utilization")
    if node_label_overlap_count:
        warning_issue_codes.append("diagram_node_label_overlap")
    if missing_drafting_field_count:
        warning_issue_codes.append("diagram_drafting_metadata_missing")
    if duplicate_drawing_number_count:
        warning_issue_codes.append("diagram_duplicate_drawing_number")
    if duplicate_sheet_number_count:
        warning_issue_codes.append("diagram_duplicate_sheet_number")
    if missing_title_block_count:
        warning_issue_codes.append("diagram_title_block_missing")
    if title_block_overlap_count:
        warning_issue_codes.append("diagram_title_block_overlap")
    if bac_pfd_mode and benchmark_cleanliness_score < 0.86:
        warning_issue_codes.append("bac_pfd_cleanliness_below_target")
    if bac_pfd_mode and route_crossings:
        warning_issue_codes.append("bac_pfd_route_crossings")
    if bac_pfd_mode and max_sheet_utilization_fraction > 0.80:
        warning_issue_codes.append("bac_pfd_high_sheet_utilization")
    if bac_pfd_mode and node_label_overlap_count:
        warning_issue_codes.append("bac_pfd_label_clearance_warning")

    if diagram_kind == "bfd":
        if missing_nodes or missing_edges or mismatched_labels:
            blocking_issue_codes.append("diagram_topology_incomplete")
        if duplicate_drawing_number_count or duplicate_sheet_number_count:
            blocking_issue_codes.append("diagram_drafting_identity_duplicate")
        if missing_title_block_count:
            blocking_issue_codes.append("diagram_title_block_missing")
        if title_block_overlap_count:
            blocking_issue_codes.append("diagram_title_block_overlap")
    else:
        if node_overlap_count:
            blocking_issue_codes.append("diagram_node_overlap")
        if node_label_overlap_count >= 6:
            blocking_issue_codes.append("diagram_excessive_label_overlap")
        if benchmark_cleanliness_score < 0.55:
            blocking_issue_codes.append("diagram_cleanliness_blocked")
        if routing is not None and sum(sheet.congested_connector_count for sheet in routing.sheets) >= 3:
            blocking_issue_codes.append("diagram_route_congestion_blocked")
        if max_sheet_utilization_fraction > 0.92:
            blocking_issue_codes.append("diagram_sheet_utilization_blocked")
        if len(missing_nodes) >= 3:
            blocking_issue_codes.append("diagram_topology_incomplete")
        if duplicate_drawing_number_count or duplicate_sheet_number_count:
            blocking_issue_codes.append("diagram_drafting_identity_duplicate")
        if missing_title_block_count:
            blocking_issue_codes.append("diagram_title_block_missing")
        if title_block_overlap_count:
            blocking_issue_codes.append("diagram_title_block_overlap")
        if bac_pfd_mode and benchmark_cleanliness_score < 0.72:
            blocking_issue_codes.append("bac_pfd_cleanliness_blocked")
        if bac_pfd_mode and route_crossings >= 2:
            blocking_issue_codes.append("bac_pfd_route_crossings_blocked")
        if bac_pfd_mode and max_sheet_utilization_fraction > 0.88:
            blocking_issue_codes.append("bac_pfd_sheet_utilization_blocked")
        if bac_pfd_mode and node_label_overlap_count >= 2:
            blocking_issue_codes.append("bac_pfd_label_clearance_blocked")

    if blocking_issue_codes:
        overall_status = "blocked"
    elif (
        warning_issue_codes
        or node_overlap_count
        or node_label_overlap_count
        or crowded_sheet_count
        or max_sheet_utilization_fraction > 0.86
        or missing_drafting_field_count
        or duplicate_drawing_number_count
        or duplicate_sheet_number_count
        or missing_title_block_count
        or title_block_overlap_count
    ):
        overall_status = "conditional"
    markdown = (
        f"### {diagram_kind.upper()} Acceptance\n\n"
        f"- Overall status: {overall_status}\n"
        f"- Missing required nodes: {', '.join(missing_nodes) or 'none'}\n"
        f"- Missing required edges: {', '.join(missing_edges) or 'none'}\n"
        f"- Label mismatches: {', '.join(mismatched_labels) or 'none'}\n"
        f"- Benchmark cleanliness score: {benchmark_cleanliness_score:.2f}\n"
        f"- Node overlaps: {node_overlap_count}\n"
        f"- Node-label overlaps: {node_label_overlap_count}\n"
        f"- Crowded sheets: {crowded_sheet_count}\n"
        f"- Max sheet utilization: {max_sheet_utilization_fraction:.0%}\n"
        f"- Missing drafting fields: {missing_drafting_field_count}\n"
        f"- Duplicate drawing numbers: {duplicate_drawing_number_count}\n"
        f"- Duplicate sheet numbers: {duplicate_sheet_number_count}\n"
        f"- Missing title blocks: {missing_title_block_count}\n"
        f"- Title-block overlaps: {title_block_overlap_count}\n"
        f"- Route crossings: {route_crossings}\n"
        f"- Route congestion channels: {route_congestion}\n"
        f"- Max routing channel load: {max_channel_load}\n"
        f"- Warning issue codes: {', '.join(warning_issue_codes) or 'none'}\n"
        f"- Blocking issue codes: {', '.join(blocking_issue_codes) or 'none'}\n"
    )
    return DiagramAcceptanceArtifact(
        diagram_id=diagram_id,
        diagram_kind="bfd" if diagram_kind == "bfd" else "pfd",
        overall_status=overall_status,
        missing_required_nodes=missing_nodes,
        missing_required_edges=missing_edges,
        mismatched_labels=mismatched_labels,
        benchmark_cleanliness_score=benchmark_cleanliness_score,
        node_overlap_count=node_overlap_count,
        node_label_overlap_count=node_label_overlap_count,
        crowded_sheet_count=crowded_sheet_count,
        max_sheet_utilization_fraction=max_sheet_utilization_fraction,
        missing_drafting_field_count=missing_drafting_field_count,
        duplicate_drawing_number_count=duplicate_drawing_number_count,
        duplicate_sheet_number_count=duplicate_sheet_number_count,
        missing_title_block_count=missing_title_block_count,
        title_block_overlap_count=title_block_overlap_count,
        warning_issue_codes=warning_issue_codes,
        blocking_issue_codes=blocking_issue_codes,
        notes=notes,
        markdown=markdown,
        citations=(blueprint.citations if blueprint is not None else [])
        or (flowsheet_graph.citations if flowsheet_graph is not None else [])
        or [],
        assumptions=(blueprint.assumptions if blueprint is not None else [])
        or (flowsheet_graph.assumptions if flowsheet_graph is not None else [])
        or [],
    )


def build_bac_diagram_benchmark_artifact(
    *,
    route_id: str,
    target: DiagramTargetProfile,
    bfd: BlockFlowDiagramArtifact,
    pfd: ProcessFlowDiagramArtifact,
    pfd_acceptance: DiagramAcceptanceArtifact,
    pid: PidLiteDiagramArtifact,
    drawio_document: str,
) -> BACDiagramBenchmarkArtifact:
    if not _is_bac_target(target):
        return BACDiagramBenchmarkArtifact(
            artifact_id=f"{route_id}_bac_diagram_benchmark",
            route_id=route_id,
            overall_status="conditional",
            rows=[],
            benchmark_labels=["non_bac_target"],
            markdown="### BAC Diagram Benchmark\n\n- Benchmark unavailable for non-BAC target.\n",
        )

    rows: list[BACDiagramBenchmarkRow] = []

    bfd_checks: list[str] = []
    bfd_failures: list[str] = []
    bfd_svg = bfd.sheets[0].svg if bfd.sheets else ""
    section_labels = [node.labels[0].text for node in bfd.nodes[:7] if node.labels]
    if "Quaternization Reaction" in section_labels:
        bfd_checks.append("locked_reaction_section")
    else:
        bfd_failures.append("missing_locked_reaction_section")
    if "Product Storage" in section_labels:
        bfd_checks.append("locked_storage_section")
    else:
        bfd_failures.append("missing_locked_storage_section")
    if "DRAFTING TITLE BLOCK" in bfd_svg:
        bfd_checks.append("title_block_present")
    else:
        bfd_failures.append("missing_title_block")
    rows.append(
        BACDiagramBenchmarkRow(
            diagram_kind="bfd",
            status="pass" if not bfd_failures else "fail",
            checks_passed=bfd_checks,
            blocking_codes=bfd_failures,
            summary="BAC BFD matches the locked section backbone." if not bfd_failures else "BAC BFD benchmark drift detected.",
        )
    )

    pfd_checks: list[str] = []
    pfd_warnings: list[str] = []
    pfd_failures: list[str] = []
    pfd_titles = [sheet.title for sheet in pfd.sheets]
    combined_pfd_svg = "\n".join(sheet.svg for sheet in pfd.sheets)
    if "BAC PFD Panel 1: Feed, Reaction, and Cleanup" in pfd_titles and "BAC PFD Panel 2: Purification, Storage, and Offsites" in pfd_titles:
        pfd_checks.append("stitched_panel_titles_locked")
    else:
        pfd_failures.append("missing_bac_pfd_panel_titles")
    if "Panel 2: Purification," in combined_pfd_svg:
        pfd_checks.append("continuation_markers_present")
    else:
        pfd_failures.append("missing_stitched_continuation_markers")
    if pfd_acceptance.overall_status == "complete":
        pfd_checks.append("acceptance_complete")
    elif pfd_acceptance.overall_status == "conditional":
        pfd_warnings.append("bac_pfd_acceptance_conditional")
    else:
        pfd_failures.append("bac_pfd_acceptance_blocked")
    if any(code.startswith("bac_pfd_") for code in pfd_acceptance.blocking_issue_codes):
        pfd_failures.append("bac_pfd_specific_blockers_present")
    rows.append(
        BACDiagramBenchmarkRow(
            diagram_kind="pfd",
            status="fail" if pfd_failures else ("warning" if pfd_warnings else "pass"),
            checks_passed=pfd_checks,
            warning_codes=pfd_warnings,
            blocking_codes=pfd_failures,
            summary="BAC PFD benchmark passes stitched-sheet and acceptance checks." if not pfd_failures else "BAC PFD benchmark drift detected.",
        )
    )

    pid_checks: list[str] = []
    pid_failures: list[str] = []
    pid_titles = [sheet.title for sheet in pid.sheets]
    combined_pid_svg = "\n".join(sheet.svg for sheet in pid.sheets)
    expected_pid_titles = {
        "BAC Reaction P&ID: Reactor",
        "BAC Purification P&ID: Purification Column",
        "BAC Storage P&ID: Product Storage",
    }
    if expected_pid_titles.issubset(set(pid_titles)):
        pid_checks.append("required_pid_titles_present")
    else:
        pid_failures.append("missing_required_pid_titles")
    if "PSV-" in combined_pid_svg or "Pressure Relief Valve" in combined_pid_svg:
        pid_checks.append("relief_coverage_visible")
    else:
        pid_failures.append("missing_relief_visibility")
    if any("BAC P&amp;ID Panel" in sheet.svg for sheet in pid.sheets):
        pid_checks.append("stitched_panel_annotations_present")
    else:
        pid_failures.append("missing_pid_panel_annotations")
    rows.append(
        BACDiagramBenchmarkRow(
            diagram_kind="pid",
            status="pass" if not pid_failures else "fail",
            checks_passed=pid_checks,
            blocking_codes=pid_failures,
            summary="BAC P&ID benchmark passes title, relief, and stitched-panel checks." if not pid_failures else "BAC P&ID benchmark drift detected.",
        )
    )

    drawio_checks: list[str] = []
    drawio_failures: list[str] = []
    drawio_tokens = [
        ('id="layer_equipment"', "equipment_layer_present"),
        ('id="layer_streams"', "streams_layer_present"),
        ('id="layer_annotations"', "annotations_layer_present"),
        ("BAC PFD Panel 1: Feed, Reaction, and Cleanup", "panel_1_annotation_present"),
        ("BAC PFD Panel 2: Purification, Storage, and Offsites", "panel_2_annotation_present"),
        ("Continues to: sheet_2", "forward_stitch_note_present"),
        ("Continues from: sheet_1", "backward_stitch_note_present"),
        ('id="n_sheet_1_reactor"', "stable_node_id_present"),
    ]
    for token, check_name in drawio_tokens:
        if token in drawio_document:
            drawio_checks.append(check_name)
        else:
            drawio_failures.append(check_name.replace("_present", "_missing"))
    rows.append(
        BACDiagramBenchmarkRow(
            diagram_kind="drawio",
            status="pass" if not drawio_failures else "fail",
            checks_passed=drawio_checks,
            blocking_codes=drawio_failures,
            summary="BAC Draw.io export preserves layers, stitch notes, and stable identities." if not drawio_failures else "BAC Draw.io benchmark drift detected.",
        )
    )

    overall_status = "complete"
    if any(row.status == "fail" for row in rows):
        overall_status = "blocked"
    elif any(row.status == "warning" for row in rows):
        overall_status = "conditional"
    markdown_lines = [
        "### BAC Diagram Benchmark",
        "",
        f"- Overall status: {overall_status}",
    ]
    for row in rows:
        markdown_lines.append(
            f"- {row.diagram_kind.upper()}: {row.status} | checks={len(row.checks_passed)} warnings={len(row.warning_codes)} blockers={len(row.blocking_codes)}"
        )
    return BACDiagramBenchmarkArtifact(
        artifact_id=f"{route_id}_bac_diagram_benchmark",
        route_id=route_id,
        overall_status=overall_status,
        rows=rows,
        benchmark_labels=[
            "benzalkonium_chloride",
            "locked_bfd_structure",
            "stitched_bac_pfd",
            "locked_bac_pid",
            "editable_drawio_layers",
        ],
        markdown="\n".join(markdown_lines) + "\n",
    )


def build_bac_drawing_package_artifact(
    *,
    route_id: str,
    target: DiagramTargetProfile,
    bfd: BlockFlowDiagramArtifact,
    pfd: ProcessFlowDiagramArtifact,
    pid: PidLiteDiagramArtifact,
    benchmark: BACDiagramBenchmarkArtifact | None = None,
    control: ControlSystemDiagramArtifact | None = None,
    base_output_dir: str = "diagrams",
) -> BACDrawingPackageArtifact:
    if not _is_bac_target(target):
        return BACDrawingPackageArtifact(
            artifact_id=f"{route_id}_bac_drawing_package",
            route_id=route_id,
            overall_status="conditional",
            benchmark_status="non_bac_target",
            package_notes=["BAC drawing package requested for non-BAC target."],
            markdown="### BAC Drawing Package\n\n- Package unavailable for non-BAC target.\n",
        )

    register_rows: list[BACDrawingRegisterRow] = []
    svg_paths: list[str] = []
    drawio_paths = [
        f"{base_output_dir}/bfd.drawio",
        f"{base_output_dir}/pfd.drawio",
        f"{base_output_dir}/pid_lite.drawio",
    ]
    if control is not None:
        drawio_paths.append(f"{base_output_dir}/control_system.drawio")

    def register_sheets(diagram_kind: str, sheets: list[DiagramSheet], svg_name_prefix: str, drawio_path: str) -> None:
        for index, sheet in enumerate(sheets, start=1):
            svg_path = f"{base_output_dir}/{svg_name_prefix}_sheet_{index}.svg"
            svg_paths.append(svg_path)
            register_rows.append(
                BACDrawingRegisterRow(
                    diagram_kind=diagram_kind,
                    sheet_id=sheet.sheet_id,
                    title=sheet.title,
                    drawing_number=sheet.drawing_number,
                    sheet_number=sheet.sheet_number,
                    issue_status=sheet.issue_status,
                    checked_by=sheet.checked_by,
                    reviewed_by=sheet.reviewed_by,
                    approved_by=sheet.approved_by,
                    approved_date=sheet.approved_date,
                    svg_path=svg_path,
                    drawio_path=drawio_path,
                    citations=[],
                    assumptions=[],
                )
            )

    register_sheets("bfd", bfd.sheets, "bfd", f"{base_output_dir}/bfd.drawio")
    register_sheets("pfd", pfd.sheets, "pfd", f"{base_output_dir}/pfd.drawio")
    register_sheets("pid", pid.sheets, "pid_lite", f"{base_output_dir}/pid_lite.drawio")
    if control is not None:
        register_sheets("control", control.sheets, "control_system", f"{base_output_dir}/control_system.drawio")

    package_notes = [
        "SVG remains the source of truth for the BAC drawing package.",
        "Draw.io exports are provided for editable review markup.",
        "Drawing register rows track per-sheet title, drawing number, and expected export path.",
    ]
    benchmark_status = benchmark.overall_status if benchmark is not None else "unverified"
    all_sheets = list(bfd.sheets) + list(pfd.sheets) + list(pid.sheets) + (list(control.sheets) if control is not None else [])
    review_workflow_status = _resolve_bac_package_review_workflow_status(all_sheets)
    revision_history = sorted(
        {
            f"{sheet.revision}:{sheet.issue_status}"
            for sheet in all_sheets
            if sheet.revision or sheet.issue_status
        }
    )
    checker = next((sheet.checked_by for sheet in all_sheets if sheet.checked_by), "")
    reviewer = next((sheet.reviewed_by for sheet in all_sheets if sheet.reviewed_by), "")
    approver = next((sheet.approved_by for sheet in all_sheets if sheet.approved_by), "")
    if benchmark is not None and benchmark.overall_status != "complete":
        package_notes.append(f"BAC benchmark status is {benchmark.overall_status}; package should not be treated as final issue.")
    overall_status = "complete"
    if benchmark is not None:
        overall_status = benchmark.overall_status

    markdown_lines = [
        "### BAC Drawing Package",
        "",
        f"- Overall status: {overall_status}",
        f"- Benchmark status: {benchmark_status}",
        f"- Review workflow status: {review_workflow_status}",
        f"- SVG sheets: {len(svg_paths)}",
        f"- Draw.io packages: {len(drawio_paths)}",
        "",
        "| Kind | Sheet | Drawing No. | Status | Title | SVG | Draw.io |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in register_rows:
        markdown_lines.append(
            f"| {row.diagram_kind.upper()} | {row.sheet_number or row.sheet_id} | {row.drawing_number or 'n/a'} | {row.issue_status or 'n/a'} | {row.title} | {row.svg_path} | {row.drawio_path} |"
        )
    return BACDrawingPackageArtifact(
        artifact_id=f"{route_id}_bac_drawing_package",
        route_id=route_id,
        overall_status=overall_status,
        benchmark_status=benchmark_status,
        review_workflow_status=review_workflow_status,
        revision_history=revision_history,
        checker=checker,
        reviewer=reviewer,
        approver=approver,
        svg_paths=svg_paths,
        drawio_paths=drawio_paths,
        register_rows=register_rows,
        package_notes=package_notes,
        markdown="\n".join(markdown_lines) + "\n",
    )


def build_bac_rendering_audit_artifact(
    *,
    route_id: str,
    target: DiagramTargetProfile,
    bfd: BlockFlowDiagramArtifact,
    pfd: ProcessFlowDiagramArtifact,
    pfd_acceptance: DiagramAcceptanceArtifact,
    pfd_routing: DiagramRoutingArtifact | None,
    pid: PidLiteDiagramArtifact,
    pid_routing: DiagramRoutingArtifact | None = None,
) -> BACRenderingAuditArtifact:
    if not _is_bac_target(target):
        return BACRenderingAuditArtifact(
            artifact_id=f"{route_id}_bac_rendering_audit",
            route_id=route_id,
            overall_status="conditional",
            audit_scope=["non_bac_target"],
            markdown="### BAC Rendering Audit\n\n- Audit unavailable for non-BAC target.\n",
        )

    rows: list[BACRenderingAuditRow] = []

    bfd_missing_fields, _, _, bfd_missing_title_blocks, bfd_title_overlap = _diagram_drafting_quality_metrics(bfd.sheets, bfd.nodes)
    bfd_findings: list[str] = []
    bfd_status = "pass"
    if bfd_missing_fields:
        bfd_findings.append("missing_drafting_fields")
        bfd_status = "warning"
    if bfd_missing_title_blocks:
        bfd_findings.append("missing_title_blocks")
        bfd_status = "fail"
    if bfd_title_overlap:
        bfd_findings.append("title_block_overlap")
        bfd_status = "fail"
    rows.append(
        BACRenderingAuditRow(
            diagram_kind="bfd",
            status=bfd_status,
            sheet_count=len(bfd.sheets),
            benchmark_cleanliness_score=1.0,
            missing_title_block_count=bfd_missing_title_blocks,
            title_block_overlap_count=bfd_title_overlap,
            findings=bfd_findings,
            summary="BAC BFD rendering audit passed." if bfd_status == "pass" else "BAC BFD rendering needs attention.",
        )
    )

    pfd_route_crossings = sum(sheet.crossing_count for sheet in (pfd_routing.sheets if pfd_routing is not None else []))
    pfd_route_congestion = sum(sheet.congested_connector_count for sheet in (pfd_routing.sheets if pfd_routing is not None else []))
    pfd_max_channel_load = max((sheet.max_channel_load for sheet in (pfd_routing.sheets if pfd_routing is not None else [])), default=0)
    pfd_continuation_markers = sum(len(sheet.continuation_markers) for sheet in (pfd_routing.sheets if pfd_routing is not None else []))
    pfd_findings = list(pfd_acceptance.warning_issue_codes)
    pfd_status = "pass"
    if pfd_acceptance.overall_status == "conditional":
        pfd_status = "warning"
    elif pfd_acceptance.overall_status == "blocked":
        pfd_status = "fail"
    rows.append(
        BACRenderingAuditRow(
            diagram_kind="pfd",
            status=pfd_status,
            sheet_count=len(pfd.sheets),
            benchmark_cleanliness_score=pfd_acceptance.benchmark_cleanliness_score,
            route_crossings=pfd_route_crossings,
            route_congestion=pfd_route_congestion,
            max_channel_load=pfd_max_channel_load,
            continuation_marker_count=pfd_continuation_markers,
            missing_title_block_count=pfd_acceptance.missing_title_block_count,
            title_block_overlap_count=pfd_acceptance.title_block_overlap_count,
            findings=pfd_findings,
            summary="BAC PFD routing and rendering audit passed." if pfd_status == "pass" else "BAC PFD routing/rendering needs attention.",
        )
    )

    pid_missing_fields, _, _, pid_missing_title_blocks, pid_title_overlap = _diagram_drafting_quality_metrics(pid.sheets, pid.nodes)
    pid_route_crossings = sum(sheet.crossing_count for sheet in (pid_routing.sheets if pid_routing is not None else []))
    pid_route_congestion = sum(sheet.congested_connector_count for sheet in (pid_routing.sheets if pid_routing is not None else []))
    pid_max_channel_load = max((sheet.max_channel_load for sheet in (pid_routing.sheets if pid_routing is not None else [])), default=0)
    pid_continuation_marker_count = sum(sheet.svg.count("&gt;&gt;") + sheet.svg.count("&lt;&lt;") for sheet in pid.sheets)
    pid_findings: list[str] = []
    pid_status = "pass"
    if pid_missing_fields:
        pid_findings.append("missing_drafting_fields")
        pid_status = "warning"
    if pid_missing_title_blocks:
        pid_findings.append("missing_title_blocks")
        pid_status = "fail"
    if pid_title_overlap:
        pid_findings.append("title_block_overlap")
        pid_status = "fail"
    if not any("Pressure Relief Valve" in sheet.svg or "PSV-" in sheet.svg for sheet in pid.sheets):
        pid_findings.append("relief_visibility_missing")
        pid_status = "fail"
    rows.append(
        BACRenderingAuditRow(
            diagram_kind="pid",
            status=pid_status,
            sheet_count=len(pid.sheets),
            benchmark_cleanliness_score=max(0.0, 1.0 - pid_route_crossings * 0.02 - pid_route_congestion * 0.03),
            route_crossings=pid_route_crossings,
            route_congestion=pid_route_congestion,
            max_channel_load=pid_max_channel_load,
            continuation_marker_count=pid_continuation_marker_count,
            missing_title_block_count=pid_missing_title_blocks,
            title_block_overlap_count=pid_title_overlap,
            findings=pid_findings,
            summary="BAC P&ID-lite rendering audit passed." if pid_status == "pass" else "BAC P&ID-lite rendering needs attention.",
        )
    )

    overall_status = "complete"
    if any(row.status == "fail" for row in rows):
        overall_status = "blocked"
    elif any(row.status == "warning" for row in rows):
        overall_status = "conditional"
    markdown_lines = [
        "### BAC Rendering Audit",
        "",
        f"- Overall status: {overall_status}",
    ]
    for row in rows:
        markdown_lines.append(
            f"- {row.diagram_kind.upper()}: {row.status} | sheets={row.sheet_count} cleanliness={row.benchmark_cleanliness_score:.2f} crossings={row.route_crossings} congestion={row.route_congestion} continuations={row.continuation_marker_count}"
        )
    return BACRenderingAuditArtifact(
        artifact_id=f"{route_id}_bac_rendering_audit",
        route_id=route_id,
        overall_status=overall_status,
        rows=rows,
        audit_scope=[
            "title_block_presence",
            "title_block_overlap",
            "pfd_routing_crossings",
            "pfd_channel_congestion",
            "continuation_marker_visibility",
            "pid_relief_visibility",
        ],
        markdown="\n".join(markdown_lines) + "\n",
    )


def _resolve_bac_package_review_workflow_status(sheets: list[DiagramSheet]) -> str:
    statuses = {sheet.issue_status.strip().lower() for sheet in sheets if sheet.issue_status.strip()}
    if not statuses:
        return "draft"
    if any(status == "as built" for status in statuses):
        return "as_built"
    if all(status == "approved" for status in statuses):
        return "approved"
    if any(status in {"for review", "approved", "as built"} for status in statuses):
        return "for_review"
    return "draft"


def _diagram_drafting_quality_metrics(
    sheets: list[DiagramSheet],
    nodes: list[DiagramNode],
) -> tuple[int, int, int, int, int]:
    node_lookup = {node.node_id: node for node in nodes}
    missing_field_count = 0
    missing_title_block_count = 0
    title_block_overlap_count = 0
    drawing_numbers: list[str] = []
    sheet_numbers: list[str] = []

    for sheet in sheets:
        required_values = [
            sheet.drawing_number,
            sheet.sheet_number,
            sheet.revision,
            sheet.revision_date,
            sheet.issue_status,
            sheet.prepared_by,
        ]
        missing_field_count += sum(1 for value in required_values if not str(value).strip())
        if sheet.drawing_number.strip():
            drawing_numbers.append(sheet.drawing_number.strip().upper())
        if sheet.sheet_number.strip():
            sheet_numbers.append(sheet.sheet_number.strip().upper())
        if sheet.svg.strip() and "DRAFTING TITLE BLOCK" not in sheet.svg:
            missing_title_block_count += 1
        title_block_rect = _diagram_title_block_rect(sheet)
        for node_id in sheet.node_ids:
            node = node_lookup.get(node_id)
            if node is None:
                continue
            if _rectangles_overlap(title_block_rect, (node.x, node.y, node.width, node.height), padding=8.0):
                title_block_overlap_count += 1

    duplicate_drawing_number_count = len(drawing_numbers) - len(set(drawing_numbers))
    duplicate_sheet_number_count = len(sheet_numbers) - len(set(sheet_numbers))
    return (
        missing_field_count,
        duplicate_drawing_number_count,
        duplicate_sheet_number_count,
        missing_title_block_count,
        title_block_overlap_count,
    )


def _diagram_title_block_rect(sheet: DiagramSheet) -> tuple[float, float, float, float]:
    width = 430.0
    height = 86.0
    x = max(8.0, sheet.width_px - width - 16.0)
    y = max(8.0, sheet.height_px - height - 14.0)
    return (x, y, width, height)


def _diagram_cleanliness_metrics(
    nodes: list[DiagramNode],
    sheets: list[DiagramSheet],
    *,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
) -> tuple[int, int, int, float, float]:
    node_lookup = {node.node_id: node for node in nodes}
    node_overlap_count = 0
    node_label_overlap_count = 0
    crowded_sheet_count = 0
    max_utilization = 0.0
    for sheet in sheets:
        sheet_nodes = [node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup]
        for left_index, left in enumerate(sheet_nodes):
            for right in sheet_nodes[left_index + 1 :]:
                if _rectangles_overlap((left.x, left.y, left.width, left.height), (right.x, right.y, right.width, right.height), padding=1.0):
                    node_overlap_count += 1
        label_bounds = _node_label_bounds_for_rendering(sheet_nodes, sheet.title)
        for left_index, left in enumerate(label_bounds):
            for right in label_bounds[left_index + 1 :]:
                if _rectangles_overlap(left, right, padding=2.0):
                    node_label_overlap_count += 1
        occupied_area = sum(node.width * node.height for node in sheet_nodes)
        utilization = occupied_area / max(1.0, float(sheet.width_px * sheet.height_px))
        if sheet_composition is not None:
            composition_sheet = next((item for item in sheet_composition.sheets if item.sheet_id == sheet.sheet_id), None)
            if composition_sheet is not None:
                packed_area = sum(placement.width * placement.height for placement in composition_sheet.module_placements)
                utilization = max(utilization, packed_area / max(1.0, float(sheet.width_px * sheet.height_px)))
                distinct_rows = {round(placement.y, 1) for placement in composition_sheet.module_placements}
                row_span = 0.0
                if composition_sheet.module_placements:
                    row_span = (
                        max(placement.x + placement.width for placement in composition_sheet.module_placements)
                        - min(placement.x for placement in composition_sheet.module_placements)
                    ) / max(1.0, float(sheet.width_px))
                if len(composition_sheet.module_placements) >= 3 and len(distinct_rows) == 1 and utilization > 0.52:
                    crowded_sheet_count += 1
                if len(composition_sheet.module_placements) >= 4 and len(distinct_rows) == 1 and row_span > 0.78:
                    crowded_sheet_count += 1
                if len(composition_sheet.module_placements) >= 4 and utilization > 0.58:
                    crowded_sheet_count += 1
        max_utilization = max(max_utilization, utilization)
    penalties = (
        node_overlap_count * 0.35
        + node_label_overlap_count * 0.18
        + crowded_sheet_count * 0.12
        + max(0.0, max_utilization - 0.55) * 0.9
    )
    cleanliness_score = max(0.0, 1.0 - penalties)
    return (
        node_overlap_count,
        node_label_overlap_count,
        crowded_sheet_count,
        max_utilization,
        cleanliness_score,
    )


def diagram_svg_fence(svg: str) -> str:
    return f"```diagram-svg\n{svg}\n```"


def build_drawio_document(
    *,
    diagram_id: str,
    title: str,
    sheets: list[DiagramSheet],
    nodes: list[DiagramNode] | None = None,
    edges: list[DiagramEdge] | None = None,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
    routing: DiagramRoutingArtifact | None = None,
    control_plan: ControlPlanArtifact | None = None,
    control_review: ControlCauseEffectArtifact | None = None,
) -> str:
    synthesized_nodes: list[DiagramNode] = []
    synthesized_edges: list[DiagramEdge] = []
    if (
        control_plan is not None
        and modules is not None
        and sheet_composition is not None
        and nodes is None
        and edges is None
    ):
        synthesized_nodes, synthesized_edges = _build_control_drawio_overlay_content(control_plan, modules, sheet_composition)
    node_lookup = {node.node_id: node for node in (nodes or [])}
    if synthesized_nodes:
        node_lookup.update({node.node_id: node for node in synthesized_nodes})
    edge_lookup = {edge.edge_id: edge for edge in (edges or [])}
    if synthesized_edges:
        edge_lookup.update({edge.edge_id: edge for edge in synthesized_edges})
    module_lookup = {module.module_id: module for module in (modules.modules if modules is not None else [])}
    drawio_layer_mode = any(
        sheet.stitch_panel_title.strip() or "bac " in sheet.title.lower()
        for sheet in sheets
    )
    pages: list[str] = []
    for page_index, sheet in enumerate(sheets, start=1):
        composition_sheet = None
        routing_sheet = None
        if sheet_composition is not None:
            composition_sheet = next((item for item in sheet_composition.sheets if item.sheet_id == sheet.sheet_id), None)
        if routing is not None:
            routing_sheet = next((item for item in routing.sheets if item.sheet_id == sheet.sheet_id), None)
        cells = [
            '<mxCell id="0"/>',
            '<mxCell id="1" parent="0"/>',
        ]
        if drawio_layer_mode:
            cells.extend(_drawio_layer_cells())
        cell_index = 2
        cells.append(
            _drawio_drafting_title_block_cell(
                page_index=page_index,
                sheet=sheet,
                cell_index=cell_index,
                parent="layer_annotations" if drawio_layer_mode else "1",
            )
        )
        cell_index += 1
        if drawio_layer_mode:
            stitch_cells, cell_index = _drawio_stitch_panel_cells(page_index=page_index, sheet=sheet, start_index=cell_index)
            cells.extend(stitch_cells)
        page_node_ids = list(sheet.node_ids)
        page_edge_ids = list(sheet.edge_ids)
        if control_plan is not None and not page_node_ids and sheet.sheet_id == "sheet_2":
            page_node_ids = [node.node_id for node in synthesized_nodes]
            page_edge_ids = [edge.edge_id for edge in synthesized_edges if edge.sheet_id == sheet.sheet_id]

        if composition_sheet is not None:
            for placement in composition_sheet.module_placements:
                module = module_lookup.get(placement.module_id)
                label = (module.title if module is not None else placement.module_id).replace("_", " ")
                cells.append(
                    _drawio_vertex_cell(
                        cell_id=f"m_{_drawio_stable_id(sheet.sheet_id, placement.module_id)}",
                        value=label,
                        x=placement.x,
                        y=placement.y,
                        width=placement.width,
                        height=placement.height,
                        style="rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#cbd5e1;fillColor=#f8fafc;fontStyle=1;",
                        parent="layer_annotations" if drawio_layer_mode else "1",
                    )
                )
                cell_index += 1

        if "p&id-lite" in sheet.title.lower() or "pid-lite" in sheet.title.lower():
            legend_cells, cell_index = _drawio_pid_lite_legend_cells(
                page_index=page_index,
                start_index=cell_index,
                sheet=sheet,
                nodes=[node_lookup[node_id] for node_id in sheet.node_ids if node_id in node_lookup],
                edges=[edge_lookup[edge_id] for edge_id in sheet.edge_ids if edge_id in edge_lookup],
                parent="layer_annotations" if drawio_layer_mode else "1",
            )
            cells.extend(legend_cells)
        if "interlocks and permissives" in sheet.title.lower() or "shutdowns and protective trips" in sheet.title.lower():
            control_cells, cell_index = _drawio_control_review_cells(
                page_index=page_index,
                start_index=cell_index,
                sheet=sheet,
            )
            cells.extend(control_cells)
            if control_plan is not None and composition_sheet is not None and modules is not None:
                content_cells, cell_index = _drawio_control_review_content_cells(
                    page_index=page_index,
                    start_index=cell_index,
                    sheet=sheet,
                    control_plan=control_plan,
                    control_review=control_review,
                    modules=modules,
                    composition_sheet=composition_sheet,
                )
                cells.extend(content_cells)

        node_cell_ids: dict[str, str] = {}
        route_hint_lookup = {
            hint.edge_id: hint
            for hint in (routing_sheet.route_hints if routing_sheet is not None else [])
        }
        for node_id in page_node_ids:
            node = node_lookup.get(node_id)
            if node is None:
                continue
            cell_id = f"n{page_index}_{cell_index}"
            stable_cell_id = f"n_{_drawio_stable_id(sheet.sheet_id, node.node_id)}"
            node_cell_ids[node.node_id] = stable_cell_id
            label_lines = [node.label]
            if node.equipment_tag:
                label_lines.insert(0, node.equipment_tag)
            secondary = [item.text for item in node.labels if item.kind in {"secondary", "utility"} and item.text]
            label_lines.extend(secondary[:2])
            cells.append(
                _drawio_vertex_cell(
                    cell_id=stable_cell_id,
                    value="&#xa;".join(_drawio_escape(item) for item in label_lines if item),
                    x=node.x,
                    y=node.y,
                    width=node.width,
                    height=node.height,
                    style=_drawio_node_style(node),
                    parent="layer_equipment" if drawio_layer_mode else "1",
                )
            )
            cell_index += 1

        for edge_id in page_edge_ids:
            edge = edge_lookup.get(edge_id)
            if edge is None:
                continue
            source_id = node_cell_ids.get(edge.source_node_id)
            target_id = node_cell_ids.get(edge.target_node_id)
            if source_id is None or target_id is None:
                continue
            label = edge.label or edge.condition_label
            geometry_points: list[tuple[float, float]] | None = None
            route_hint = route_hint_lookup.get(edge.edge_id)
            if route_hint is not None:
                geometry_points = [(point.x, point.y) for point in route_hint.points]
            source_node = node_lookup.get(edge.source_node_id)
            target_node = node_lookup.get(edge.target_node_id)
            source_port_role = _edge_note_value(edge.notes, "source_port_role")
            target_port_role = _edge_note_value(edge.notes, "target_port_role")
            cells.append(
                _drawio_edge_cell(
                    cell_id=f"e_{_drawio_stable_id(sheet.sheet_id, edge.edge_id)}",
                    value=label,
                    source=source_id,
                    target=target_id,
                    style=_drawio_edge_style(
                        edge,
                        source_node,
                        target_node,
                        source_side=_template_port_side_for_node(source_node, source_port_role),
                        target_side=_template_port_side_for_node(target_node, target_port_role),
                        source_port_role=source_port_role,
                        target_port_role=target_port_role,
                    ),
                    geometry_points=geometry_points,
                    parent="layer_streams" if drawio_layer_mode else "1",
                )
            )
            cell_index += 1

        root_xml = "".join(cells)
        pages.append(
            (
                f'<diagram id="{_drawio_escape(sheet.sheet_id)}" name="{_drawio_escape(sheet.title)}">'
                f'<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
                f'pageScale="1" pageWidth="{sheet.width_px}" pageHeight="{sheet.height_px}" math="0" shadow="0">'
                f"<root>{root_xml}</root>"
                f"</mxGraphModel>"
                f"</diagram>"
            )
        )

    pages_xml = "".join(pages)
    return (
        f'<mxfile host="app.diagrams.net" version="24.7.17" type="device" agent="AoC" modified="{_drawio_escape(diagram_id)}">'
        f"{pages_xml}"
        f"</mxfile>"
    )


def _drawio_escape(value: str) -> str:
    return html.escape(value, quote=True)


def _drawio_stable_id(*parts: str) -> str:
    raw = "_".join(part.strip().lower() for part in parts if part.strip())
    cleaned = re.sub(r"[^a-z0-9_]+", "_", raw)
    return cleaned.strip("_") or "cell"


def _drawio_vertex_cell(
    *,
    cell_id: str,
    value: str,
    x: float,
    y: float,
    width: float,
    height: float,
    style: str,
    parent: str = "1",
) -> str:
    return (
        f'<mxCell id="{cell_id}" value="{value}" style="{style}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" as="geometry"/>'
        f"</mxCell>"
    )


def _drawio_drafting_title_block_cell(*, page_index: int, sheet: DiagramSheet, cell_index: int, parent: str = "1") -> str:
    fields = [
        "DRAFTING TITLE BLOCK",
        f"Drawing: {sheet.drawing_number or sheet.sheet_id}",
        f"Sheet: {sheet.sheet_number or sheet.sheet_id}",
        f"Rev: {sheet.revision or 'A'}",
        f"Status: {sheet.issue_status or 'For Review'}",
        f"Date: {sheet.revision_date or utc_now()[:10]}",
        f"By: {sheet.prepared_by or 'AoC'}",
    ]
    value = "&#xa;".join(_drawio_escape(field) for field in fields)
    return _drawio_vertex_cell(
        cell_id=f"tb_{_drawio_stable_id(sheet.sheet_id, str(page_index), str(cell_index))}",
        value=value,
        x=max(8.0, sheet.width_px - 440.0),
        y=max(8.0, sheet.height_px - 102.0),
        width=420.0,
        height=82.0,
        style=(
            "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#111827;"
            "fontSize=10;align=left;verticalAlign=top;spacing=6;fontStyle=0;"
        ),
        parent=parent,
    )


def _drawio_edge_cell(
    *,
    cell_id: str,
    value: str,
    source: str,
    target: str,
    style: str,
    geometry_points: list[tuple[float, float]] | None = None,
    parent: str = "1",
) -> str:
    geometry = '<mxGeometry relative="1" as="geometry"/>'
    if geometry_points and len(geometry_points) > 2:
        waypoint_xml = "".join(
            f'<mxPoint x="{point[0]:.1f}" y="{point[1]:.1f}"/>'
            for point in geometry_points[1:-1]
        )
        geometry = (
            '<mxGeometry relative="1" as="geometry">'
            f'<Array as="points">{waypoint_xml}</Array>'
            "</mxGeometry>"
        )
    return (
        f'<mxCell id="{cell_id}" value="{_drawio_escape(value)}" style="{style}" edge="1" parent="{parent}" source="{source}" target="{target}">'
        f"{geometry}"
        "</mxCell>"
    )


def _drawio_layer_cells() -> list[str]:
    return [
        '<mxCell id="layer_equipment" value="Equipment Layer" style="group;html=1;" vertex="1" connectable="0" parent="1"><mxGeometry x="0" y="0" width="0" height="0" as="geometry"/></mxCell>',
        '<mxCell id="layer_streams" value="Streams Layer" style="group;html=1;" vertex="1" connectable="0" parent="1"><mxGeometry x="0" y="0" width="0" height="0" as="geometry"/></mxCell>',
        '<mxCell id="layer_annotations" value="Annotations Layer" style="group;html=1;" vertex="1" connectable="0" parent="1"><mxGeometry x="0" y="0" width="0" height="0" as="geometry"/></mxCell>',
    ]


def _drawio_stitch_panel_cells(*, page_index: int, sheet: DiagramSheet, start_index: int) -> tuple[list[str], int]:
    if not any([sheet.stitch_panel_title.strip(), sheet.stitch_prev_sheet_id.strip(), sheet.stitch_next_sheet_id.strip()]):
        return [], start_index
    lines = [sheet.stitch_panel_title or sheet.title]
    if sheet.stitch_prev_sheet_id:
        lines.append(f"Continues from: {sheet.stitch_prev_sheet_id}")
    if sheet.stitch_next_sheet_id:
        lines.append(f"Continues to: {sheet.stitch_next_sheet_id}")
    cells = [
        _drawio_vertex_cell(
            cell_id=f"sp_{_drawio_stable_id(sheet.sheet_id, str(page_index), str(start_index))}",
            value="&#xa;".join(_drawio_escape(line) for line in lines),
            x=58.0,
            y=54.0,
            width=360.0,
            height=max(52.0, 18.0 + 16.0 * len(lines)),
            style=(
                "rounded=0;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;"
                "fontSize=10;align=left;verticalAlign=middle;spacing=8;fontStyle=1;"
            ),
            parent="layer_annotations",
        )
    ]
    return cells, start_index + 1


def _drawio_port_anchor(side: str) -> tuple[float, float]:
    normalized = side.strip().lower()
    if normalized == "left":
        return (0.0, 0.5)
    if normalized == "right":
        return (1.0, 0.5)
    if normalized == "top":
        return (0.5, 0.0)
    if normalized == "bottom":
        return (0.5, 1.0)
    return (1.0, 0.5)


def _drawio_port_anchor_for_node(node: DiagramNode | None, side: str, port_role: str = "") -> tuple[float, float]:
    if node is not None and port_role:
        point = _template_port_geometry(node, side, port_role)
        if point is not None and node.width > 0 and node.height > 0:
            return ((point[0] - node.x) / node.width, (point[1] - node.y) / node.height)
    return _drawio_port_anchor(side)


def _drawio_node_style(node: DiagramNode) -> str:
    lowered = node.node_family.lower()
    shape = "rounded=1"
    if "column" in lowered:
        shape = "shape=cylinder3"
    elif "controller" in lowered:
        shape = "rhombus"
    elif "instrument" in lowered:
        shape = "ellipse"
    elif "valve" in lowered:
        shape = "rhombus"
    elif "pump" in lowered or "compressor" in lowered:
        shape = "ellipse"
    elif "exchanger" in lowered or "condenser" in lowered:
        shape = "shape=hexagon;perimeter=hexagonPerimeter2"
    elif "terminal" in lowered:
        shape = "shape=mxgraph.flowchart.terminator"
    return f"{shape};whiteSpace=wrap;html=1;strokeColor=#1f2937;fillColor=#ffffff;align=center;verticalAlign=middle;"


def _drawio_edge_style(
    edge: DiagramEdge,
    source_node: DiagramNode | None = None,
    target_node: DiagramNode | None = None,
    *,
    source_side: str = "",
    target_side: str = "",
    source_port_role: str = "",
    target_port_role: str = "",
) -> str:
    stroke = "#111111"
    dashed = "0"
    if edge.edge_type == "recycle":
        stroke = "#5d6d7e"
        dashed = "1"
    elif edge.edge_type == "control_signal":
        stroke = "#8b1e3f"
        dashed = "1"
    elif edge.edge_type == "safeguard":
        stroke = "#c2410c"
        dashed = "1"
    elif edge.edge_type in {"purge", "vent"}:
        stroke = "#6b7280"
        dashed = "1"
    elif edge.edge_type == "waste":
        stroke = "#7f1d1d"
        dashed = "1"
    elif edge.edge_type == "utility":
        stroke = "#4a6fa5"
        dashed = "1"
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeColor={stroke};dashed={dashed};endArrow=block;endFill=1;"
    )
    if not source_side and source_node is not None:
        source_side = _edge_note_value(source_node.notes, "pid_attach_side")
    if not target_side and target_node is not None:
        target_side = _edge_note_value(target_node.notes, "pid_attach_side")
    if source_side:
        exit_x, exit_y = _drawio_port_anchor_for_node(source_node, source_side, source_port_role)
        style += f"exitX={exit_x};exitY={exit_y};exitPerimeter=0;"
    if target_side:
        entry_x, entry_y = _drawio_port_anchor_for_node(target_node, target_side, target_port_role)
        style += f"entryX={entry_x};entryY={entry_y};entryPerimeter=0;"
    return style


def _build_control_drawio_overlay_content(
    control_plan: ControlPlanArtifact,
    modules: DiagramModuleArtifact,
    sheet_composition: DiagramSheetCompositionArtifact,
) -> tuple[list[DiagramNode], list[DiagramEdge]]:
    overlay_sheet = next((sheet for sheet in sheet_composition.sheets if sheet.sheet_id == "sheet_2"), None)
    if overlay_sheet is None:
        return [], []
    module_lookup = {module.module_id: module for module in modules.modules}
    unit_to_loops: dict[str, list[str]] = {}
    for loop in control_plan.control_loops:
        if loop.unit_id:
            unit_to_loops.setdefault(loop.unit_id, []).append(loop.control_id)
    family_guess = {
        "R-": "reactor",
        "PU-": "separator",
        "TK-": "tank",
        "P-": "pump",
        "E-": "heat exchanger",
        "D-": "column",
    }
    nodes: list[DiagramNode] = []
    for rank, placement in enumerate(overlay_sheet.module_placements):
        module = module_lookup.get(placement.module_id)
        if module is None or not module.unit_ids:
            continue
        unit_id = module.unit_ids[0]
        node_family = "separator"
        for prefix, family in family_guess.items():
            if unit_id.upper().startswith(prefix):
                node_family = family
                break
        node = DiagramNode(
            node_id=unit_id,
            label=unit_id,
            node_family=node_family,
            section_id="control_overlay",
            equipment_tag=unit_id,
            labels=[
                DiagramLabel(text=unit_id),
                DiagramLabel(text=", ".join(unit_to_loops.get(unit_id, [])[:2]), kind="secondary"),
            ],
            layout=DiagramLayoutHints(rank=rank),
        )
        _apply_pfd_node_dimensions(node)
        node.x = placement.x + max(18.0, (placement.width - node.width) / 2)
        node.y = placement.y + max(20.0, (placement.height - node.height) / 2)
        nodes.append(node)
    edges: list[DiagramEdge] = []
    for index, (left, right) in enumerate(zip(nodes, nodes[1:]), start=1):
        edges.append(
            DiagramEdge(
                edge_id=f"overlay_edge_{index}",
                source_node_id=left.node_id,
                target_node_id=right.node_id,
                edge_type="main",
                label="Control interaction path",
                sheet_id="sheet_2",
            )
        )
    return nodes, edges


def _drawio_pid_lite_legend_cells(
    *,
    page_index: int,
    start_index: int,
    sheet: DiagramSheet,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    parent: str = "1",
) -> tuple[list[str], int]:
    x = max(980.0, float(sheet.width_px) - 350.0)
    y = 104.0
    line_classes: list[str] = []
    for edge in edges:
        if edge.condition_label and edge.condition_label not in line_classes:
            line_classes.append(edge.condition_label)
    line_classes = line_classes[:3]

    loop_tags: list[str] = []
    for node in nodes:
        for label in node.labels:
            if label.kind == "utility" and label.text and label.text not in loop_tags:
                loop_tags.append(label.text)
    loop_tags = loop_tags[:4]

    symbol_entries: list[str] = []
    family_labels = [
        ("instrument", "Instrument bubble"),
        ("controller", "Local controller"),
        ("valve", "Valve / final element"),
        ("relief_valve", "Relief valve"),
        ("reactor", "Unit anchor"),
        ("column", "Unit anchor"),
        ("vessel", "Unit anchor"),
        ("separator", "Unit anchor"),
        ("tank", "Unit anchor"),
        ("heat exchanger", "Unit anchor"),
    ]
    node_families = {node.node_family for node in nodes}
    for family, label in family_labels:
        if family in node_families and label not in symbol_entries:
            symbol_entries.append(label)
    symbol_entries = symbol_entries[:4]

    cells: list[str] = []
    box_height = 112 + max(len(line_classes), 1) * 12 + max(len(loop_tags), 1) * 12 + max(len(symbol_entries), 1) * 12
    legend_id = f"l{page_index}_{start_index}"
    cells.append(
        _drawio_vertex_cell(
            cell_id=legend_id,
            value="P&amp;ID-LITE LEGEND",
            x=x,
            y=y,
            width=270.0,
            height=float(box_height),
            style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#56606b;fillColor=#fdfefe;fontStyle=1;align=center;verticalAlign=top;spacingTop=8;",
            parent=parent,
        )
    )
    cell_index = start_index + 1
    cursor_y = y + 34.0
    sections = [
        ("Line Classes", line_classes or ["See inline line tags"]),
        ("Loop Tags", loop_tags or ["Local loop IDs shown on bubbles"]),
        ("Symbols", symbol_entries or ["Unit anchor", "Instrument bubble", "Valve / final element"]),
    ]
    for title, items in sections:
        cells.append(
            _drawio_vertex_cell(
                cell_id=f"l{page_index}_{cell_index}",
                value=_drawio_escape(title),
                x=x + 12.0,
                y=cursor_y,
                width=246.0,
                height=14.0,
                style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontStyle=1;fontSize=10;",
                parent=parent,
            )
        )
        cell_index += 1
        cursor_y += 16.0
        for item in items:
            cells.append(
                _drawio_vertex_cell(
                    cell_id=f"l{page_index}_{cell_index}",
                    value=_drawio_escape(item),
                    x=x + 14.0,
                    y=cursor_y,
                    width=242.0,
                    height=12.0,
                    style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=9;",
                    parent=parent,
                )
            )
            cell_index += 1
            cursor_y += 12.0
        cursor_y += 6.0
    return cells, cell_index


def _drawio_control_review_cells(
    *,
    page_index: int,
    start_index: int,
    sheet: DiagramSheet,
) -> tuple[list[str], int]:
    x = max(980.0, float(sheet.width_px) - 350.0)
    y = 96.0
    if "shutdowns and protective trips" in sheet.title.lower():
        title = "SHUTDOWN REVIEW"
        sections = [
            ("Review Focus", ["Trip cause", "Shutdown action", "Protected final action"]),
            ("Intent", ["Safety-critical loops only", "Focused shutdown/trip review"]),
        ]
    else:
        title = "CONTROL REVIEW"
        sections = [
            ("Matrix Columns", ["Cause / permissive", "Action / shutdown", "Override", "Safeguard / trip"]),
            ("Intent", ["Operator logic separated from protective trips"]),
        ]
    cells: list[str] = []
    box_height = 94 + sum(len(items) for _, items in sections) * 12
    cells.append(
        _drawio_vertex_cell(
            cell_id=f"cr{page_index}_{start_index}",
            value=title,
            x=x,
            y=y,
            width=270.0,
            height=float(box_height),
            style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#56606b;fillColor=#fdfefe;fontStyle=1;align=center;verticalAlign=top;spacingTop=8;",
        )
    )
    cell_index = start_index + 1
    cursor_y = y + 34.0
    for section_title, items in sections:
        cells.append(
            _drawio_vertex_cell(
                cell_id=f"cr{page_index}_{cell_index}",
                value=_drawio_escape(section_title),
                x=x + 12.0,
                y=cursor_y,
                width=246.0,
                height=14.0,
                style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontStyle=1;fontSize=10;",
            )
        )
        cell_index += 1
        cursor_y += 16.0
        for item in items:
            cells.append(
                _drawio_vertex_cell(
                    cell_id=f"cr{page_index}_{cell_index}",
                    value=_drawio_escape(item),
                    x=x + 14.0,
                    y=cursor_y,
                    width=242.0,
                    height=12.0,
                    style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=9;",
                )
            )
            cell_index += 1
            cursor_y += 12.0
        cursor_y += 6.0
    return cells, cell_index


def _drawio_control_review_content_cells(
    *,
    page_index: int,
    start_index: int,
    sheet: DiagramSheet,
    control_plan: ControlPlanArtifact,
    control_review: ControlCauseEffectArtifact | None,
    modules: DiagramModuleArtifact,
    composition_sheet: DiagramSheetComposition,
) -> tuple[list[str], int]:
    row_lookup: dict[str, list[ControlCauseEffectRow]] = {}
    if control_review is not None:
        for row in control_review.rows:
            if row.unit_id:
                row_lookup.setdefault(row.unit_id, []).append(row)
    else:
        for loop in control_plan.control_loops:
            if loop.unit_id:
                row_lookup.setdefault(loop.unit_id, []).append(
                    ControlCauseEffectRow(
                        control_id=loop.control_id,
                        unit_id=loop.unit_id,
                        controlled_variable=loop.controlled_variable,
                        cause_permissive=loop.startup_logic or "Standard startup permissive",
                        action_shutdown=loop.shutdown_logic or "Standard shutdown rundown",
                        override_logic=loop.override_logic or "Basic operator override",
                        safeguard_trip=loop.safeguard_linkage or "No dedicated trip linkage",
                        protected_final_action=loop.manipulated_variable or loop.actuator or "Protective action",
                        criticality=loop.criticality or "medium",
                        safety_critical=bool(loop.safeguard_linkage or (loop.criticality or "").lower() == "high"),
                    )
                )
    module_lookup = {module.module_id: module for module in modules.modules}
    cells: list[str] = []
    cell_index = start_index
    is_shutdown = "shutdowns and protective trips" in sheet.title.lower()
    for placement in composition_sheet.module_placements:
        module = module_lookup.get(placement.module_id)
        if module is None:
            continue
        unit_id = next((item for item in module.unit_ids if item), "")
        rows = row_lookup.get(unit_id, [])
        if is_shutdown:
            rows = [row for row in rows if row.safety_critical or row.action_shutdown or row.safeguard_trip != "No dedicated trip linkage"]
        if not rows:
            continue
        base_y = placement.y + 34.0
        for row in rows[: (2 if is_shutdown else 3)]:
            summary_lines = [row.control_id]
            if is_shutdown:
                summary_lines.extend(
                    [
                        f"Trip cause: {row.safeguard_trip or row.controlled_variable}",
                        f"Shutdown action: {row.action_shutdown or 'Standard shutdown rundown'}",
                        f"Protected final action: {row.protected_final_action or 'Protective action'}",
                    ]
                )
            else:
                summary_lines.extend(
                    [
                        f"Cause / permissive: {row.cause_permissive or 'Standard startup permissive'}",
                        f"Action / shutdown: {row.action_shutdown or 'Standard shutdown rundown'}",
                        f"Override: {row.override_logic or 'Basic operator override'}",
                        f"Safeguard / trip: {row.safeguard_trip or 'No dedicated trip linkage'}",
                    ]
                )
            cells.append(
                _drawio_vertex_cell(
                    cell_id=f"cc{page_index}_{cell_index}",
                    value="&#xa;".join(_drawio_escape(item) for item in summary_lines),
                    x=placement.x + 18.0,
                    y=base_y,
                    width=placement.width - 36.0,
                    height=60.0 if is_shutdown else 74.0,
                    style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#94a3b8;fillColor=#ffffff;align=left;verticalAlign=middle;spacingLeft=8;",
                )
            )
            cell_index += 1
            base_y += 70.0 if is_shutdown else 82.0
    return cells, cell_index


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
    if any(token in lowered for token in ("storage", "dispatch", "pack", "tankage")):
        return "storage"
    if any(token in lowered for token in ("waste", "effluent", "scrub", "vent")):
        return "waste handling"
    return lowered.strip() or "process section"


def _display_bfd_section(section_key: str, *, target: DiagramTargetProfile | None = None) -> str:
    if target is not None and _is_bac_target(target):
        return _bac_bfd_display_label_map().get(section_key, section_key.title().replace("Bfd", "BFD").replace("Pfd", "PFD"))
    return section_key.title().replace("Bfd", "BFD").replace("Pfd", "PFD")


def _ordered_bfd_sections(section_keys, target: DiagramTargetProfile) -> list[str]:
    ordered = list(dict.fromkeys(str(section_key) for section_key in section_keys if str(section_key).strip()))
    if _is_bac_target(target):
        priority = _bac_bfd_section_order()
        ranked = [section for section in priority if section in ordered or section in set(target.required_bfd_sections)]
        extras = [section for section in ordered if section not in ranked]
        return ranked + extras
    return ordered


def _bac_bfd_section_order() -> list[str]:
    return [
        "feed preparation",
        "reaction",
        "cleanup",
        "concentration",
        "purification",
        "storage",
        "waste handling",
    ]


def _bac_bfd_display_label_map() -> dict[str, str]:
    return {
        "feed preparation": "Feed Preparation",
        "reaction": "Quaternization Reaction",
        "cleanup": "Primary Cleanup",
        "concentration": "Concentration",
        "purification": "Purification",
        "storage": "Product Storage",
        "waste handling": "Waste Handling",
    }


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


def _layout_bac_bfd_nodes(nodes: list[DiagramNode], style: DiagramStyleProfile) -> None:
    if not nodes:
        return
    width = 248.0
    height = 82.0
    gap = 30.0
    x = max(180.0, (760.0 - width) / 2)
    y = 126.0
    for node in nodes:
        node.width = width
        node.height = height
        node.x = x
        node.y = y
        y += height + gap


def _pfd_node_family(unit_type: str, label: str) -> str:
    return _equipment_template_for_text(unit_type, label, build_diagram_equipment_templates()).node_family


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
            "waste_treatment": ("ETP-401", "Integrated ETP / Waste Management", "bac_waste_receiver"),
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


def _build_pfd_sheets_from_composition(
    nodes: list[DiagramNode],
    modules: DiagramModuleArtifact,
    composition: DiagramSheetCompositionArtifact,
    style: DiagramStyleProfile,
    target: DiagramTargetProfile,
) -> list[DiagramSheet]:
    node_lookup = {node.node_id: node for node in nodes}
    module_lookup = {module.module_id: module for module in modules.modules}
    sheets: list[DiagramSheet] = []
    for composition_sheet in composition.sheets:
        node_ids: list[str] = []
        for placement in composition_sheet.module_placements:
            module = module_lookup.get(placement.module_id)
            if module is None:
                continue
            module_nodes = [node_lookup[node_id] for node_id in module.entity_ids if node_id in node_lookup]
            if not module_nodes:
                continue
            _layout_module_nodes(module_nodes, placement, module=module)
            node_ids.extend(node.node_id for node in module_nodes)
        sheet = DiagramSheet(
            sheet_id=composition_sheet.sheet_id,
            title=composition_sheet.title,
            width_px=composition_sheet.width_px,
            height_px=composition_sheet.height_px,
            stitch_panel_id=composition_sheet.stitch_panel_id,
            stitch_panel_title=composition_sheet.stitch_panel_title,
            stitch_prev_sheet_id=composition_sheet.stitch_prev_sheet_id,
            stitch_next_sheet_id=composition_sheet.stitch_next_sheet_id,
            orientation="landscape",
            presentation_mode="sheet",
            preferred_scale=1.0,
            full_page=True,
            legend_mode="embedded",
            suppress_inline_wrapping=True,
            node_ids=node_ids,
        )
        sheet_node_lookup = {node_id: node_lookup[node_id] for node_id in node_ids if node_id in node_lookup}
        if _is_bac_target(target):
            if len(sheet_node_lookup) == 5:
                _apply_bac_single_sheet_pfd_layout(sheet, list(sheet_node_lookup.values()))
            else:
                _apply_bac_pfd_layout(sheet, list(sheet_node_lookup.values()))
        if sheet_node_lookup:
            max_x = max(node.x + node.width for node in sheet_node_lookup.values())
            max_y = max(node.y + node.height for node in sheet_node_lookup.values())
            sheet.width_px = max(sheet.width_px, int(max_x + 220))
            sheet.height_px = max(sheet.height_px, int(max_y + 180))
        sheets.append(sheet)
    if sheets:
        return sheets
    return _build_pfd_sheets(nodes, style, target)


def _build_pfd_edges_from_semantics(
    semantics: PlantDiagramSemanticsArtifact,
    modules: DiagramModuleArtifact,
    composition: DiagramSheetCompositionArtifact,
    stream_index: dict[str, object],
    sheets: list[DiagramSheet],
    target: DiagramTargetProfile,
) -> list[DiagramEdge]:
    del target
    module_by_entity: dict[str, str] = {}
    for module in modules.modules:
        for entity_id in module.entity_ids:
            module_by_entity[entity_id] = module.module_id
    entity_lookup = {entity.entity_id: entity for entity in semantics.entities}
    templates = build_diagram_equipment_templates()
    module_to_sheet = {
        placement.module_id: sheet.sheet_id
        for sheet in composition.sheets
        for placement in sheet.module_placements
    }
    valid_sheet_ids = {sheet.sheet_id for sheet in sheets}
    edges: list[DiagramEdge] = []
    for edge_counter, connection in enumerate(semantics.connections, start=1):
        source_module_id = module_by_entity.get(connection.source_entity_id)
        target_module_id = module_by_entity.get(connection.target_entity_id)
        if not source_module_id or not target_module_id:
            continue
        source_sheet_id = module_to_sheet.get(source_module_id)
        target_sheet_id = module_to_sheet.get(target_module_id)
        if not source_sheet_id or source_sheet_id != target_sheet_id or source_sheet_id not in valid_sheet_ids:
            continue
        source_stream = stream_index.get(connection.stream_id) if connection.stream_id else None
        label = connection.label
        condition_label = connection.condition_label
        if source_stream is not None and not label:
            label = _pfd_stream_label(source_stream.stream_id, source_stream.description, source_stream.stream_role)
        if source_stream is not None and not condition_label and connection.role == DiagramEdgeRole.PROCESS:
            if source_stream.temperature_c and source_stream.pressure_bar:
                condition_label = f"{source_stream.temperature_c:.0f} C / {source_stream.pressure_bar:.1f} bar"
        notes = f"lane={connection.preferred_lane};connection={connection.connection_id}"
        context_text = ""
        if source_stream is not None:
            context_text = " ".join(part for part in [source_stream.description, source_stream.stream_role] if part)
        notes = _append_note_value(
            notes,
            "source_port_role",
            _connection_template_port_role(entity_lookup.get(connection.source_entity_id), connection, "out", templates, context_text),
        )
        notes = _append_note_value(
            notes,
            "target_port_role",
            _connection_template_port_role(entity_lookup.get(connection.target_entity_id), connection, "in", templates, context_text),
        )
        edges.append(
            DiagramEdge(
                edge_id=f"pfd_edge_{edge_counter}",
                source_node_id=connection.source_entity_id,
                target_node_id=connection.target_entity_id,
                edge_type=_edge_type_from_diagram_role(connection.role),
                stream_id=connection.stream_id,
                label=label,
                condition_label=condition_label,
                sheet_id=source_sheet_id,
                notes=notes,
            )
        )
    return edges


def _build_pfd_sheet_continuation_markers(
    sheet_id: str,
    semantics: PlantDiagramSemanticsArtifact,
    modules: DiagramModuleArtifact,
    composition: DiagramSheetCompositionArtifact,
) -> list[dict[str, object]]:
    sheet_titles = {
        sheet.sheet_id: (sheet.stitch_panel_title if sheet.stitch_panel_title.strip() else sheet.sheet_id)
        for sheet in composition.sheets
    }
    module_by_entity: dict[str, str] = {}
    for module in modules.modules:
        for entity_id in module.entity_ids:
            module_by_entity[entity_id] = module.module_id
    placement_lookup = {
        (sheet.sheet_id, placement.module_id): placement
        for sheet in composition.sheets
        for placement in sheet.module_placements
    }
    module_to_sheet = {
        placement.module_id: sheet.sheet_id
        for sheet in composition.sheets
        for placement in sheet.module_placements
    }
    markers: list[dict[str, object]] = []
    for connection in semantics.connections:
        source_module_id = module_by_entity.get(connection.source_entity_id)
        target_module_id = module_by_entity.get(connection.target_entity_id)
        if not source_module_id or not target_module_id:
            continue
        source_sheet_id = module_to_sheet.get(source_module_id)
        target_sheet_id = module_to_sheet.get(target_module_id)
        if not source_sheet_id or not target_sheet_id or source_sheet_id == target_sheet_id:
            continue
        if sheet_id == source_sheet_id:
            placement = placement_lookup.get((source_sheet_id, source_module_id))
            if placement is None:
                continue
            markers.append(
                {
                    "x": placement.x + placement.width + 22.0,
                    "y": placement.y + 32.0,
                    "side": "right",
                    "label": connection.label or connection.stream_id or connection.role.value.title(),
                    "target_sheet": sheet_titles.get(target_sheet_id, target_sheet_id),
                }
            )
        elif sheet_id == target_sheet_id:
            placement = placement_lookup.get((target_sheet_id, target_module_id))
            if placement is None:
                continue
            markers.append(
                {
                    "x": max(26.0, placement.x - 22.0),
                    "y": placement.y + 32.0,
                    "side": "left",
                    "label": connection.label or connection.stream_id or connection.role.value.title(),
                    "target_sheet": sheet_titles.get(source_sheet_id, source_sheet_id),
                }
            )
    return markers


def _build_pid_sheet_continuation_markers(
    sheet_id: str,
    semantics: PlantDiagramSemanticsArtifact,
    modules: DiagramModuleArtifact,
    composition: DiagramSheetCompositionArtifact,
) -> list[dict[str, object]]:
    connection_lookup = {connection.connection_id: connection for connection in semantics.connections}
    module_order = {
        placement.module_id: index
        for index, sheet in enumerate(composition.sheets)
        for placement in sheet.module_placements
    }
    placement_lookup = {
        (sheet.sheet_id, placement.module_id): placement
        for sheet in composition.sheets
        for placement in sheet.module_placements
    }
    module_to_sheet = {
        placement.module_id: sheet.sheet_id
        for sheet in composition.sheets
        for placement in sheet.module_placements
    }
    sheet_titles = {sheet.sheet_id: sheet.stitch_panel_title or sheet.title for sheet in composition.sheets}
    markers: list[dict[str, object]] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    stream_to_modules: dict[str, list[tuple[str, str]]] = {}
    for module in modules.modules:
        stream_labels: dict[str, str] = {}
        for connection_id in module.connection_ids:
            connection = connection_lookup.get(connection_id)
            if connection is None or not connection.stream_id:
                continue
            stream_labels.setdefault(connection.stream_id, connection.label or connection.stream_id)
        for stream_id, label in stream_labels.items():
            stream_to_modules.setdefault(stream_id, []).append((module.module_id, label))

    for stream_id, module_entries in stream_to_modules.items():
        if len(module_entries) < 2:
            continue
        ordered_entries = sorted(module_entries, key=lambda item: module_order.get(item[0], 0))
        for (source_module_id, source_label), (target_module_id, target_label) in zip(ordered_entries, ordered_entries[1:]):
            source_sheet_id = module_to_sheet.get(source_module_id)
            target_sheet_id = module_to_sheet.get(target_module_id)
            if not source_sheet_id or not target_sheet_id or source_sheet_id == target_sheet_id:
                continue
            label = source_label or target_label or stream_id
            if sheet_id == source_sheet_id:
                pair_key = (sheet_id, target_sheet_id, label)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                placement = placement_lookup.get((source_sheet_id, source_module_id))
                if placement is None:
                    continue
                markers.append(
                    {
                        "x": placement.x + placement.width + 18.0,
                        "y": placement.y + placement.height / 2,
                        "side": "right",
                        "label": label,
                        "target_sheet": sheet_titles.get(target_sheet_id, target_sheet_id),
                    }
                )
            elif sheet_id == target_sheet_id:
                pair_key = (sheet_id, source_sheet_id, label)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                placement = placement_lookup.get((target_sheet_id, target_module_id))
                if placement is None:
                    continue
                markers.append(
                    {
                        "x": max(28.0, placement.x - 18.0),
                        "y": placement.y + placement.height / 2,
                        "side": "left",
                        "label": label,
                        "target_sheet": sheet_titles.get(source_sheet_id, source_sheet_id),
                    }
                )
    return markers


def _build_pfd_sheet_route_hints(
    sheet_id: str,
    edges: list[DiagramEdge],
    nodes: list[DiagramNode],
    modules: DiagramModuleArtifact,
    composition: DiagramSheetCompositionArtifact,
    target: DiagramTargetProfile | None = None,
) -> dict[str, dict[str, object]]:
    node_lookup = {node.node_id: node for node in nodes}
    module_lookup = {module.module_id: module for module in modules.modules}
    module_by_entity: dict[str, str] = {}
    for module in modules.modules:
        for entity_id in module.entity_ids:
            module_by_entity[entity_id] = module.module_id
    composition_sheet = next((sheet for sheet in composition.sheets if sheet.sheet_id == sheet_id), None)
    if composition_sheet is None:
        return {}
    placement_lookup = {placement.module_id: placement for placement in composition_sheet.module_placements}
    label_obstacles = _node_label_bounds_for_rendering(nodes, composition_sheet.title)
    connector_lookup = {
        _edge_note_value(edge.notes, "connection"): edge.edge_id
        for edge in edges
        if _edge_note_value(edge.notes, "connection")
    }
    connector_lane_reservations = _build_pfd_connector_lane_reservations(composition_sheet, modules, target)
    route_hints: dict[str, dict[str, object]] = {}
    for connector in composition_sheet.connectors:
        if connector.source_module_id == connector.target_module_id:
            continue
        edge_id = connector_lookup.get(connector.connector_id.replace("sheet_connector_", ""))
        if not edge_id:
            continue
        source_module = module_lookup.get(connector.source_module_id)
        target_module = module_lookup.get(connector.target_module_id)
        source_placement = placement_lookup.get(connector.source_module_id)
        target_placement = placement_lookup.get(connector.target_module_id)
        if source_module is None or target_module is None or source_placement is None or target_placement is None:
            continue
        source_port = next((port for port in source_module.boundary_ports if port.port_id == connector.source_port_id), None)
        target_port = next((port for port in target_module.boundary_ports if port.port_id == connector.target_port_id), None)
        if source_port is None or target_port is None:
            continue
        source_node = node_lookup.get(source_port.entity_id)
        target_node = node_lookup.get(target_port.entity_id)
        if source_node is None or target_node is None:
            continue
        reservation = connector_lane_reservations.get(connector.connector_id, {})
        points = _pfd_route_points_for_connector(
            source_node,
            target_node,
            source_placement,
            source_port,
            target_placement,
            target_port,
            preferred_mid_x=float(reservation.get("mid_x", 0.0)) if "mid_x" in reservation else None,
            preferred_lane_y=float(reservation.get("lane_y", 0.0)) if "lane_y" in reservation else None,
        )
        if not points:
            continue
        label_anchor_index = max(1, min(len(points) - 2, len(points) // 2))
        label_point = points[label_anchor_index]
        route_hints[edge_id] = {
            "points": points,
            "label": (label_point[0], label_point[1] - 12.0),
            "condition": (label_point[0], label_point[1] + 2.0),
        }
    for edge in edges:
        if edge.edge_id in route_hints:
            continue
        source_module_id = module_by_entity.get(edge.source_node_id)
        target_module_id = module_by_entity.get(edge.target_node_id)
        if not source_module_id or source_module_id != target_module_id:
            continue
        module = module_lookup.get(source_module_id)
        placement = placement_lookup.get(source_module_id)
        source_node = node_lookup.get(edge.source_node_id)
        target_node = node_lookup.get(edge.target_node_id)
        if module is None or placement is None or source_node is None or target_node is None:
            continue
        points = _pfd_route_points_within_module(source_node, target_node, placement, edge, module, obstacle_rects=label_obstacles)
        if not points:
            continue
        label_anchor_index = max(1, min(len(points) - 2, len(points) // 2))
        label_point = points[label_anchor_index]
        route_hints[edge.edge_id] = {
            "points": points,
            "label": (label_point[0], label_point[1] - 12.0),
            "condition": (label_point[0], label_point[1] + 2.0),
        }
    return _optimize_pfd_route_hints(route_hints, composition_sheet.width_px, composition_sheet.height_px)


def _build_pfd_connector_lane_reservations(
    composition_sheet: DiagramSheetComposition,
    modules: DiagramModuleArtifact,
    target: DiagramTargetProfile | None = None,
) -> dict[str, dict[str, float]]:
    module_lookup = {module.module_id: module for module in modules.modules}
    placement_lookup = {placement.module_id: placement for placement in composition_sheet.module_placements}
    reservations: dict[str, dict[str, float]] = {}
    grouped: dict[tuple[str, str, str, str], list[DiagramInterModuleConnector]] = {}
    for connector in composition_sheet.connectors:
        source_module = module_lookup.get(connector.source_module_id)
        target_module = module_lookup.get(connector.target_module_id)
        if source_module is None or target_module is None:
            continue
        source_port = next((port for port in source_module.boundary_ports if port.port_id == connector.source_port_id), None)
        target_port = next((port for port in target_module.boundary_ports if port.port_id == connector.target_port_id), None)
        if source_port is None or target_port is None:
            continue
        grouped.setdefault(
            (
                connector.source_module_id,
                connector.target_module_id,
                source_port.side.value,
                target_port.side.value,
            ),
            [],
        ).append(connector)
    for key, connectors in grouped.items():
        source_module_id, target_module_id, source_side, target_side = key
        source_placement = placement_lookup.get(source_module_id)
        target_placement = placement_lookup.get(target_module_id)
        if source_placement is None or target_placement is None:
            continue
        connectors = sorted(connectors, key=lambda item: item.connector_id)
        count = len(connectors)
        lane_y_step = float(target.connector_lane_y_spacing_px) if target is not None else 18.0
        mid_x_step = float(target.connector_mid_x_spacing_px) if target is not None else 28.0
        if source_side in {"top", "bottom"} or target_side in {"top", "bottom"}:
            base_y = (
                min(source_placement.y, target_placement.y) - 26.0
                if source_side == "top" or target_side == "top"
                else max(source_placement.y + source_placement.height, target_placement.y + target_placement.height) + 26.0
            )
            for index, connector in enumerate(connectors):
                offset = (index - (count - 1) / 2.0) * lane_y_step
                reservations[connector.connector_id] = {"lane_y": base_y + offset}
        else:
            base_mid_x = (source_placement.x + source_placement.width + target_placement.x) / 2.0
            for index, connector in enumerate(connectors):
                offset = (index - (count - 1) / 2.0) * mid_x_step
                reservations[connector.connector_id] = {"mid_x": base_mid_x + offset}
    return reservations


def _optimize_pfd_route_hints(
    route_hints: dict[str, dict[str, object]],
    sheet_width: int,
    sheet_height: int,
) -> dict[str, dict[str, object]]:
    if len(route_hints) < 2:
        return route_hints
    original = {
        edge_id: {
            "points": [tuple(point) for point in hint.get("points", [])],
            "label": hint.get("label", (0.0, 0.0)),
            "condition": hint.get("condition", (0.0, 0.0)),
        }
        for edge_id, hint in route_hints.items()
    }
    optimized: dict[str, dict[str, object]] = {}
    remaining = dict(original)
    for edge_id, hint in original.items():
        remaining.pop(edge_id, None)
        best_hint = hint
        best_score = _route_hint_set_score({**optimized, edge_id: best_hint, **remaining})
        for candidate_points in _route_hint_variants(hint["points"], sheet_width, sheet_height):
            candidate_hint = _route_hint_with_points(hint, candidate_points)
            candidate_score = _route_hint_set_score({**optimized, edge_id: candidate_hint, **remaining})
            if candidate_score + 0.1 < best_score:
                best_hint = candidate_hint
                best_score = candidate_score
        optimized[edge_id] = best_hint
    return optimized


def _pfd_route_points_for_connector(
    source_node: DiagramNode,
    target_node: DiagramNode,
    source_placement: DiagramModulePlacement,
    source_port: DiagramModulePort,
    target_placement: DiagramModulePlacement,
    target_port: DiagramModulePort,
    *,
    preferred_mid_x: float | None = None,
    preferred_lane_y: float | None = None,
) -> list[tuple[float, float]]:
    source_side = source_port.side.value
    target_side = target_port.side.value
    start = _node_connection_point(source_node, source_side, source_port.template_port_role)
    end = _node_connection_point(target_node, target_side, target_port.template_port_role)
    source_boundary = _module_port_anchor(source_placement, source_port)
    target_boundary = _module_port_anchor(target_placement, target_port)
    points: list[tuple[float, float]] = [start, source_boundary]
    if source_side in {"top", "bottom"} or target_side in {"top", "bottom"}:
        if source_side == "top" or target_side == "top":
            lane_y = preferred_lane_y if preferred_lane_y is not None else min(source_boundary[1], target_boundary[1]) - 26.0
        else:
            lane_y = preferred_lane_y if preferred_lane_y is not None else max(source_boundary[1], target_boundary[1]) + 26.0
        points.extend([(source_boundary[0], lane_y), (target_boundary[0], lane_y)])
    else:
        mid_x = preferred_mid_x if preferred_mid_x is not None else (source_boundary[0] + target_boundary[0]) / 2
        points.extend([(mid_x, source_boundary[1]), (mid_x, target_boundary[1])])
    points.extend([target_boundary, end])
    deduped: list[tuple[float, float]] = []
    for point in points:
        if not deduped or deduped[-1] != point:
            deduped.append(point)
    return deduped


def _route_hint_variants(
    points: list[tuple[float, float]],
    sheet_width: int,
    sheet_height: int,
) -> list[list[tuple[float, float]]]:
    if len(points) < 4:
        return [points]
    internal_indexes = list(range(1, len(points) - 1))
    variants: list[list[tuple[float, float]]] = [points]
    seen: set[tuple[tuple[float, float], ...]] = {tuple(points)}
    x_groups: dict[int, list[int]] = {}
    y_groups: dict[int, list[int]] = {}
    for index in internal_indexes:
        point = points[index]
        x_groups.setdefault(int(round(point[0])), []).append(index)
        y_groups.setdefault(int(round(point[1])), []).append(index)
    for coord, indexes in x_groups.items():
        if len(indexes) < 2:
            continue
        for delta in (-72.0, -48.0, -24.0, 24.0, 48.0, 72.0):
            shifted = list(points)
            new_x = max(24.0, min(float(sheet_width) - 24.0, coord + delta))
            for index in indexes:
                shifted[index] = (new_x, shifted[index][1])
            if not _points_are_axis_aligned(shifted):
                continue
            key = tuple(shifted)
            if key in seen:
                continue
            seen.add(key)
            variants.append(shifted)
    for coord, indexes in y_groups.items():
        if len(indexes) < 2:
            continue
        for delta in (-72.0, -48.0, -24.0, 24.0, 48.0, 72.0):
            shifted = list(points)
            new_y = max(24.0, min(float(sheet_height) - 24.0, coord + delta))
            for index in indexes:
                shifted[index] = (shifted[index][0], new_y)
            if not _points_are_axis_aligned(shifted):
                continue
            key = tuple(shifted)
            if key in seen:
                continue
            seen.add(key)
            variants.append(shifted)
    return variants


def _route_hint_with_points(
    hint: dict[str, object],
    points: list[tuple[float, float]],
) -> dict[str, object]:
    label_anchor_index = max(1, min(len(points) - 2, len(points) // 2))
    label_point = points[label_anchor_index]
    return {
        "points": points,
        "label": (label_point[0], label_point[1] - 12.0),
        "condition": (label_point[0], label_point[1] + 2.0),
    }


def _route_hint_set_score(route_hints: dict[str, dict[str, object]]) -> float:
    crossings, congested, max_load = _routing_quality_metrics(route_hints)
    total_length = 0.0
    for hint in route_hints.values():
        points = [(float(point[0]), float(point[1])) for point in hint.get("points", [])]
        for left, right in zip(points, points[1:]):
            total_length += abs(left[0] - right[0]) + abs(left[1] - right[1])
    return crossings * 1000.0 + congested * 200.0 + max(0, max_load - 3) * 50.0 + total_length * 0.01


def _points_are_axis_aligned(points: list[tuple[float, float]]) -> bool:
    for left, right in zip(points, points[1:]):
        if abs(left[0] - right[0]) >= 0.1 and abs(left[1] - right[1]) >= 0.1:
            return False
    return True


def _pfd_route_points_within_module(
    source_node: DiagramNode,
    target_node: DiagramNode,
    placement: DiagramModulePlacement,
    edge: DiagramEdge,
    module: DiagramModuleSpec,
    *,
    obstacle_rects: list[tuple[float, float, float, float]] | None = None,
) -> list[tuple[float, float]]:
    lane_note = _edge_note_value(edge.notes, "lane") or edge.edge_type
    source_port_role = _edge_note_value(edge.notes, "source_port_role")
    target_port_role = _edge_note_value(edge.notes, "target_port_role")
    reserved = _module_reserved_margins(module)
    top_corridor = placement.y + max(14.0, reserved["top"] * 0.55)
    bottom_corridor = placement.y + placement.height - max(14.0, reserved["bottom"] * 0.55)
    source_lane = _module_lane_index(source_node)
    target_lane = _module_lane_index(target_node)
    forward = source_node.x <= target_node.x

    if lane_note == "utility":
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "top",
            "top",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            preferred_corridor_y=top_corridor,
            obstacle_rects=obstacle_rects,
        )
    if lane_note in {"vent", "waste", "purge"}:
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "bottom",
            "bottom",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            preferred_corridor_y=bottom_corridor,
            obstacle_rects=obstacle_rects,
        )
    if lane_note == "recycle":
        corridor_y = top_corridor if not forward else max(top_corridor, min(source_node.y, target_node.y) - 26.0)
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "top",
            "top",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            preferred_corridor_y=corridor_y,
            obstacle_rects=obstacle_rects,
        )
    if source_lane == target_lane and forward:
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "right",
            "left",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            obstacle_rects=obstacle_rects,
        )
    if source_lane < target_lane:
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "bottom",
            "top",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            obstacle_rects=obstacle_rects,
        )
    if source_lane > target_lane:
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "top",
            "bottom",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            obstacle_rects=obstacle_rects,
        )
    if not forward:
        return _best_module_route(
            source_node,
            target_node,
            placement,
            "top",
            "top",
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            preferred_corridor_y=top_corridor,
            obstacle_rects=obstacle_rects,
        )
    return _best_module_route(
        source_node,
        target_node,
        placement,
        "right",
        "left",
        source_port_role=source_port_role,
        target_port_role=target_port_role,
        obstacle_rects=obstacle_rects,
    )


def _best_module_route(
    source_node: DiagramNode,
    target_node: DiagramNode,
    placement: DiagramModulePlacement,
    source_side: str,
    target_side: str,
    *,
    source_port_role: str = "",
    target_port_role: str = "",
    preferred_corridor_y: float | None = None,
    obstacle_rects: list[tuple[float, float, float, float]] | None = None,
) -> list[tuple[float, float]]:
    candidates: list[tuple[list[tuple[float, float]], float]] = []
    candidate_y_values = _candidate_module_corridors(
        source_node,
        target_node,
        placement,
        preferred_corridor_y,
        source_port_role=source_port_role,
        target_port_role=target_port_role,
    )
    if preferred_corridor_y is None and source_side not in {"top", "bottom"} and target_side not in {"top", "bottom"}:
        base_path = _orthogonal_route_between_nodes(
            source_node,
            target_node,
            source_side,
            target_side,
            source_port_role=source_port_role,
            target_port_role=target_port_role,
        )
        candidates.append((base_path, 0.0))
    for index, corridor_y in enumerate(candidate_y_values):
        path = _orthogonal_route_between_nodes(
            source_node,
            target_node,
            source_side,
            target_side,
            source_port_role=source_port_role,
            target_port_role=target_port_role,
            corridor_y=corridor_y,
        )
        bias = abs((preferred_corridor_y if preferred_corridor_y is not None else path[1][1]) - corridor_y) if len(path) > 1 else 0.0
        candidates.append((path, bias + index * 2.0))
    best_path: list[tuple[float, float]] = []
    best_score = float("inf")
    for path, bias in candidates:
        score = _route_obstacle_score(path, obstacle_rects or []) + bias
        if score < best_score:
            best_path = path
            best_score = score
    return best_path


def _candidate_module_corridors(
    source_node: DiagramNode,
    target_node: DiagramNode,
    placement: DiagramModulePlacement,
    preferred_corridor_y: float | None,
    *,
    source_port_role: str = "",
    target_port_role: str = "",
) -> list[float]:
    values: list[float] = []
    if preferred_corridor_y is not None:
        values.append(preferred_corridor_y)
    min_y = placement.y + 18.0
    max_y = placement.y + placement.height - 18.0
    start_y = _node_connection_point(
        source_node,
        "top" if source_node.y >= target_node.y else "bottom",
        source_port_role,
    )[1]
    end_y = _node_connection_point(
        target_node,
        "top" if target_node.y >= source_node.y else "bottom",
        target_port_role,
    )[1]
    mid_y = (start_y + end_y) / 2
    values.extend(
        [
            mid_y,
            mid_y - 26.0,
            mid_y + 26.0,
            min(source_node.y, target_node.y) - 24.0,
            max(source_node.y + source_node.height, target_node.y + target_node.height) + 24.0,
            min_y,
            max_y,
        ]
    )
    deduped: list[float] = []
    for value in values:
        clamped = min(max(value, min_y), max_y)
        if not any(abs(existing - clamped) < 0.1 for existing in deduped):
            deduped.append(clamped)
    return deduped


def _route_obstacle_score(
    points: list[tuple[float, float]],
    obstacle_rects: list[tuple[float, float, float, float]],
) -> float:
    score = 0.0
    for obstacle in obstacle_rects:
        if _path_intersects_rect(points, obstacle, padding=4.0):
            score += 100.0
    if len(points) >= 2:
        score += sum(abs(right[0] - left[0]) + abs(right[1] - left[1]) for left, right in zip(points, points[1:])) * 0.01
    score += max(0, len(points) - 4) * 1.5
    return score


def _orthogonal_route_between_nodes(
    source_node: DiagramNode,
    target_node: DiagramNode,
    source_side: str,
    target_side: str,
    *,
    source_port_role: str = "",
    target_port_role: str = "",
    corridor_y: float | None = None,
) -> list[tuple[float, float]]:
    start = _node_connection_point(source_node, source_side, source_port_role)
    end = _node_connection_point(target_node, target_side, target_port_role)
    points: list[tuple[float, float]] = [start]
    if corridor_y is not None:
        points.extend([(start[0], corridor_y), (end[0], corridor_y), end])
    elif source_side in {"top", "bottom"} or target_side in {"top", "bottom"}:
        mid_y = (start[1] + end[1]) / 2
        points.extend([(start[0], mid_y), (end[0], mid_y), end])
    else:
        mid_x = (start[0] + end[0]) / 2
        points.extend([(mid_x, start[1]), (mid_x, end[1]), end])
    deduped: list[tuple[float, float]] = []
    for point in points:
        if not deduped or deduped[-1] != point:
            deduped.append(point)
    return deduped


def _module_port_anchor(placement: DiagramModulePlacement, port: DiagramModulePort) -> tuple[float, float]:
    side = port.side.value
    order = max(1, port.order_index)
    if side in {"left", "right"}:
        x = placement.x if side == "left" else placement.x + placement.width
        y = placement.y + min(placement.height - 22.0, 24.0 + order * 28.0)
        return (x, y)
    x = placement.x + min(placement.width - 30.0, 30.0 + order * 34.0)
    y = placement.y if side == "top" else placement.y + placement.height
    return (x, y)


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
        _apply_pfd_node_dimensions(node)
        node.x = x
        node.y = 150 + lane * 235
        x += node.width + 92


def _apply_pfd_node_dimensions(node: DiagramNode) -> None:
    templates = build_diagram_equipment_templates()
    template_family = {
        "reactor": "reactor",
        "column": "column",
        "vessel": "vessel",
        "separator": "vessel",
        "tank": "tank",
        "heat exchanger": "heat_exchanger",
        "condenser": "heat_exchanger",
        "pump": "pump",
        "terminal": "terminal",
    }.get(node.node_family, "")
    template = next((item for item in templates.templates if item.family == template_family), None) if template_family else None
    if node.node_family in {"column", "bac_purification_column"}:
        node.width = template.default_width_px if template is not None else 150
        node.height = (template.default_height_px + 10) if template is not None else 190
    elif node.node_family == "instrument":
        node.width = 76
        node.height = 76
    elif node.node_family == "controller":
        node.width = 92
        node.height = 92
    elif node.node_family in {"valve", "relief_valve"}:
        node.width = 82
        node.height = 82
    elif node.node_family == "pump":
        node.width = (template.default_width_px + 38) if template is not None else 170
        node.height = template.default_height_px if template is not None else 92
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
        node.width = (template.default_width_px + 10) if template is not None else 190
        node.height = (template.default_height_px + 30) if template is not None else 150
    elif node.node_family == "bac_exchanger_package":
        node.width = 230
        node.height = 116
    elif node.node_family in {"heat exchanger", "condenser"}:
        node.width = (template.default_width_px + 73) if template is not None else 205
        node.height = (template.default_height_px + 32) if template is not None else 104
    elif node.node_family == "terminal":
        node.width = template.default_width_px if template is not None else 120
        node.height = template.default_height_px if template is not None else 80
    else:
        node.width = 190
        node.height = 104


def _layout_module_nodes(
    nodes: list[DiagramNode],
    placement: DiagramModulePlacement,
    *,
    module: DiagramModuleSpec | None = None,
) -> None:
    for node in nodes:
        _apply_pfd_node_dimensions(node)

    reserved = _module_reserved_margins(module)
    usable_x0 = placement.x + reserved["left"]
    usable_y0 = placement.y + reserved["top"]
    usable_width = max(80.0, placement.width - reserved["left"] - reserved["right"])
    usable_height = max(80.0, placement.height - reserved["top"] - reserved["bottom"])

    lanes: dict[int, list[DiagramNode]] = {}
    for node in sorted(nodes, key=lambda item: (_module_lane_index(item), item.layout.rank, item.equipment_tag)):
        lane = _module_lane_index(node)
        node.layout.lane = f"lane_{lane}"
        lanes.setdefault(lane, []).append(node)

    active_lane_ids = sorted(lanes)
    if not active_lane_ids:
        return

    node_footprints = {node.node_id: _node_layout_footprint(node) for node in nodes}
    lane_heights = {lane_id: max(node_footprints[node.node_id][1] for node in lane_nodes) for lane_id, lane_nodes in lanes.items()}
    total_lane_height = sum(lane_heights.values())
    lane_gap = 18.0 if len(active_lane_ids) > 1 else 0.0
    available_vertical_gap = max(0.0, usable_height - total_lane_height)
    effective_lane_gap = min(lane_gap, available_vertical_gap / max(1, len(active_lane_ids) - 1)) if len(active_lane_ids) > 1 else 0.0
    current_y = usable_y0 + max(0.0, (usable_height - (total_lane_height + effective_lane_gap * max(0, len(active_lane_ids) - 1))) / 2)

    for lane_id in active_lane_ids:
        lane_nodes = lanes[lane_id]
        lane_height = lane_heights[lane_id]
        x_positions = _module_lane_x_positions(lane_nodes, usable_x0, usable_width)
        for node, footprint_x in zip(lane_nodes, x_positions):
            footprint_width, footprint_height = node_footprints[node.node_id]
            node.x = footprint_x + max(0.0, (footprint_width - node.width) / 2)
            node.y = current_y + max(0.0, (lane_height - footprint_height) / 2)
        current_y += lane_height + effective_lane_gap


def _module_lane_index(node: DiagramNode) -> int:
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
    return family_lane.get(node.node_family, 1)


def _module_reserved_margins(module: DiagramModuleSpec | None) -> dict[str, float]:
    counts = {"left": 0, "right": 0, "top": 0, "bottom": 0}
    bonus = {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0}
    if module is not None:
        for port in module.boundary_ports:
            counts[port.side.value] = counts.get(port.side.value, 0) + 1
            role = port.template_port_role or ""
            if role in {"overhead", "safeguard", "utility_inlet", "vent"}:
                bonus[port.side.value] += 10.0
            elif role in {"bottoms", "drain", "utility_outlet"}:
                bonus[port.side.value] += 8.0
            elif role in {"measurement", "process_inlet", "process_outlet"}:
                bonus[port.side.value] += 4.0
    return {
        "left": 20.0 + min(34.0, counts["left"] * 6.0) + min(18.0, bonus["left"]),
        "right": 20.0 + min(34.0, counts["right"] * 6.0) + min(18.0, bonus["right"]),
        "top": 20.0 + min(38.0, counts["top"] * 7.0) + min(24.0, bonus["top"]),
        "bottom": 18.0 + min(34.0, counts["bottom"] * 7.0) + min(20.0, bonus["bottom"]),
    }


def _module_lane_x_positions(
    lane_nodes: list[DiagramNode],
    usable_x0: float,
    usable_width: float,
) -> list[float]:
    if not lane_nodes:
        return []
    spacings: list[float] = []
    total_width = 0.0
    for index, node in enumerate(lane_nodes):
        total_width += _node_layout_footprint(node)[0]
        if index < len(lane_nodes) - 1:
            spacings.append(_module_node_spacing(node, lane_nodes[index + 1]))
    spacing_total = sum(spacings)
    effective_scale = min(1.0, usable_width / max(1.0, total_width + spacing_total))
    scaled_spacings = [max(12.0, spacing * effective_scale) for spacing in spacings]
    rendered_width = total_width + sum(scaled_spacings)
    start_x = usable_x0 + max(0.0, (usable_width - rendered_width) / 2)
    positions: list[float] = []
    cursor = start_x
    for index, node in enumerate(lane_nodes):
        positions.append(cursor)
        cursor += _node_layout_footprint(node)[0]
        if index < len(lane_nodes) - 1:
            cursor += scaled_spacings[index]
    return positions


def _module_node_spacing(left: DiagramNode, right: DiagramNode) -> float:
    left_width, _ = _node_layout_footprint(left)
    right_width, _ = _node_layout_footprint(right)
    label_load = max(_estimate_node_label_span_px(left), _estimate_node_label_span_px(right))
    footprint_load = max(left_width - left.width, right_width - right.width, 0.0)
    return max(24.0, min(92.0, 20.0 + label_load * 0.10 + footprint_load * 0.16))


def _estimate_node_label_span_px(node: DiagramNode) -> float:
    longest_label = max((len(label.text) for label in node.labels), default=len(node.label))
    return float(max(60, longest_label * 6))


def _node_layout_footprint(node: DiagramNode) -> tuple[float, float]:
    temp_node = DiagramNode(
        node_id=node.node_id,
        label=node.label,
        node_family=node.node_family,
        section_id=node.section_id,
        equipment_tag=node.equipment_tag,
        labels=list(node.labels),
        layout=node.layout.model_copy(deep=True),
        x=0.0,
        y=0.0,
        width=node.width,
        height=node.height,
        notes=node.notes,
    )
    bounds = [(0.0, 0.0, temp_node.width, temp_node.height)]
    for label_style in _node_label_render_styles(temp_node, "module_layout"):
        bounds.append(
            _label_bounds(
                temp_node.width / 2,
                float(label_style["y"]),
                str(label_style["text"]),
                int(label_style["wrap"]),
                int(label_style["font_size"]),
            )
        )
    min_x = min(bound[0] for bound in bounds)
    min_y = min(bound[1] for bound in bounds)
    max_x = max(bound[0] + bound[2] for bound in bounds)
    max_y = max(bound[1] + bound[3] for bound in bounds)
    return (max_x - min_x, max_y - min_y)


def _layout_pid_lite_module_nodes(
    nodes: list[DiagramNode],
    placement: DiagramModulePlacement,
    entity_lookup: dict[str, PlantDiagramEntity],
) -> None:
    if not nodes:
        return
    for node in nodes:
        _apply_pfd_node_dimensions(node)
    node_lookup = {node.node_id: node for node in nodes}
    unit_nodes = [node for node in nodes if entity_lookup.get(node.node_id) and entity_lookup[node.node_id].kind == DiagramEntityKind.UNIT]
    if not unit_nodes:
        _layout_module_nodes(nodes, placement)
        return
    unit_node = unit_nodes[0]
    bac_pid_mode = any(entity.metadata.get("bac_pid_profile", "") == "true" for entity in entity_lookup.values())
    unit_node.x = placement.x + (placement.width - unit_node.width) / 2
    unit_node.y = placement.y + placement.height * (0.46 if bac_pid_mode else 0.48) - unit_node.height / 2
    unit_entity = entity_lookup.get(unit_node.node_id)
    attachment_groups: dict[str, list[DiagramNode]] = {}
    for node in nodes:
        if node.node_id == unit_node.node_id:
            continue
        entity = entity_lookup.get(node.node_id)
        if entity is None:
            continue
        attachment_groups.setdefault(entity.attachment_role or "", []).append(node)

    if bac_pid_mode:
        _apply_bac_pid_template_layout(
            unit_node=unit_node,
            unit_entity=unit_entity,
            attachment_groups=attachment_groups,
            placement=placement,
        )
        for node in nodes:
            if node.node_id == unit_node.node_id:
                continue
            entity = entity_lookup.get(node.node_id)
            if entity is None:
                continue
            role = entity.attachment_role or ""
            if role in attachment_groups:
                continue
            node.x = placement.x + 120.0 - node.width / 2
            node.y = placement.y + 120.0 - node.height / 2
        return

    process_line_step = 138.0 if bac_pid_mode else 170.0
    grouped_order = ["measurement", "local_indication", "local_control", "final_control_element", "safeguard_relief", "process_line"]
    for role in grouped_order:
        group_nodes = attachment_groups.get(role, [])
        if not group_nodes:
            continue
        for index, node in enumerate(group_nodes):
            px, py, attach_side = _pid_lite_attachment_anchor(
                unit_node,
                unit_entity,
                role=role,
                index=index,
                count=len(group_nodes),
                process_line_step=process_line_step,
                compact_mode=bac_pid_mode,
            )
            node.x = px - node.width / 2
            node.y = py - node.height / 2
            node.notes = _append_note_value(node.notes, "pid_attach_side", attach_side)

    for node in nodes:
        if node.node_id == unit_node.node_id:
            continue
        entity = entity_lookup.get(node.node_id)
        if entity is None:
            continue
        role = entity.attachment_role or ""
        if role in attachment_groups:
            continue
        fallback_x = placement.x + (92.0 if bac_pid_mode else 120.0) + len(attachment_groups) * 28.0
        fallback_y = placement.y + (98.0 if bac_pid_mode else 120.0)
        node.x = fallback_x - node.width / 2
        node.y = fallback_y - node.height / 2

    if bac_pid_mode:
        min_x = min(node.x for node in nodes)
        min_y = min(node.y for node in nodes)
        max_x = max(node.x + node.width for node in nodes)
        max_y = max(node.y + node.height for node in nodes)
        cluster_width = max_x - min_x
        cluster_height = max_y - min_y
        target_center_x = placement.x + placement.width * 0.48
        target_center_y = placement.y + placement.height * 0.46
        dx = target_center_x - (min_x + cluster_width / 2)
        dy = target_center_y - (min_y + cluster_height / 2)
        for node in nodes:
            node.x += dx
            node.y += dy


def _apply_bac_pid_template_layout(
    *,
    unit_node: DiagramNode,
    unit_entity: PlantDiagramEntity | None,
    attachment_groups: dict[str, list[DiagramNode]],
    placement: DiagramModulePlacement,
) -> None:
    del placement
    family = (unit_entity.metadata.get("template_family", "") if unit_entity is not None else "").strip().lower()
    if not family:
        family = unit_node.node_family

    center_x = unit_node.x + unit_node.width / 2
    center_y = unit_node.y + unit_node.height / 2
    left_bank_x = unit_node.x - 92.0
    right_bank_x = unit_node.x + unit_node.width + 54.0
    top_row_y = unit_node.y - 96.0
    top_ctrl_y = unit_node.y - 54.0
    top_relief_y = unit_node.y - 114.0
    bottom_line_y = unit_node.y + unit_node.height + 42.0

    if family == "column":
        left_bank_x = unit_node.x - 86.0
        right_bank_x = unit_node.x + unit_node.width + 58.0
        top_row_y = unit_node.y - 110.0
        top_ctrl_y = unit_node.y - 64.0
        top_relief_y = unit_node.y - 126.0
        bottom_line_y = unit_node.y + unit_node.height + 34.0

    measurements = sorted(attachment_groups.get("measurement", []), key=lambda node: node.equipment_tag)
    indications = sorted(attachment_groups.get("local_indication", []), key=lambda node: node.equipment_tag)
    controls = sorted(attachment_groups.get("local_control", []), key=lambda node: node.equipment_tag)
    final_elements = sorted(attachment_groups.get("final_control_element", []), key=lambda node: node.equipment_tag)
    safeguards = sorted(attachment_groups.get("safeguard_relief", []), key=lambda node: node.equipment_tag)
    process_lines = sorted(attachment_groups.get("process_line", []), key=lambda node: node.equipment_tag)

    for index, node in enumerate(measurements):
        node.x = left_bank_x - node.width / 2
        node.y = (unit_node.y + 18.0 + index * 92.0) - node.height / 2
        node.notes = _append_note_value(node.notes, "pid_attach_side", "right")

    for index, node in enumerate(indications):
        x = center_x - 112.0 + index * 76.0
        node.x = x - node.width / 2
        node.y = top_row_y - node.height / 2
        node.notes = _append_note_value(node.notes, "pid_attach_side", "bottom")

    for index, node in enumerate(controls):
        x = center_x - ((len(controls) - 1) * 92.0) / 2 + index * 92.0
        node.x = x - node.width / 2
        node.y = top_ctrl_y - node.height / 2
        node.notes = _append_note_value(node.notes, "pid_attach_side", "bottom")

    for index, node in enumerate(final_elements):
        node.x = right_bank_x - node.width / 2
        node.y = (unit_node.y + 28.0 + index * 96.0) - node.height / 2
        node.notes = _append_note_value(node.notes, "pid_attach_side", "left")

    for index, node in enumerate(safeguards):
        x = unit_node.x + unit_node.width + 18.0 + index * 54.0
        node.x = x - node.width / 2
        node.y = top_relief_y - node.height / 2
        node.notes = _append_note_value(node.notes, "pid_attach_side", "bottom")

    for index, node in enumerate(process_lines):
        x = center_x - ((len(process_lines) - 1) * 120.0) / 2 + index * 120.0
        node.x = x - node.width / 2
        node.y = bottom_line_y - node.height / 2
        node.notes = _append_note_value(node.notes, "pid_attach_side", "top")


def _pid_lite_attachment_anchor(
    unit_node: DiagramNode,
    unit_entity: PlantDiagramEntity | None,
    *,
    role: str,
    index: int,
    count: int,
    process_line_step: float,
    compact_mode: bool = False,
) -> tuple[float, float, str]:
    unit_family_text = (unit_entity.metadata.get("unit_type", "") if unit_entity is not None else "").lower()
    node_family = unit_node.node_family
    family = (unit_entity.metadata.get("template_family", "") if unit_entity is not None else "").strip().lower()
    if not family:
        family = "reactor" if "reactor" in unit_family_text or node_family == "reactor" else node_family
        if "column" in unit_family_text or node_family == "column":
            family = "column"
        elif any(token in unit_family_text for token in {"exchanger", "heater", "cooler", "condenser", "reboiler"}) or node_family == "heat exchanger":
            family = "heat_exchanger"
        elif any(token in unit_family_text for token in {"tank", "vessel", "separator", "flash"}) or node_family in {"vessel", "separator", "tank"}:
            family = "vessel"

    center_x = unit_node.x + unit_node.width / 2
    center_y = unit_node.y + unit_node.height / 2
    top_y = unit_node.y - (30.0 if compact_mode else 38.0)
    lower_y = unit_node.y + unit_node.height + (30.0 if compact_mode else 38.0)
    left_x = unit_node.x - (56.0 if compact_mode else 72.0)
    right_x = unit_node.x + unit_node.width + (56.0 if compact_mode else 72.0)

    if role == "measurement":
        row, lane = _pid_lite_fan_slot(index, count, per_lane=3)
        if family == "column":
            return (unit_node.x - (52.0 if compact_mode else 64.0) - lane * (44.0 if compact_mode else 58.0), unit_node.y + 28.0 + row * (68.0 if compact_mode else 82.0), "left")
        if family == "heat_exchanger":
            return (unit_node.x + 40.0 + row * (74.0 if compact_mode else 92.0), unit_node.y - (42.0 if compact_mode else 56.0) - lane * (40.0 if compact_mode else 54.0), "top")
        return (left_x - lane * (44.0 if compact_mode else 58.0), unit_node.y + 24.0 + row * (72.0 if compact_mode else 90.0), "left")
    if role == "final_control_element":
        row, lane = _pid_lite_fan_slot(index, count, per_lane=3)
        if family == "column":
            return (
                unit_node.x + unit_node.width + (52.0 if compact_mode else 64.0) + lane * (44.0 if compact_mode else 58.0),
                unit_node.y + unit_node.height - 28.0 - row * (68.0 if compact_mode else 82.0),
                "right",
            )
        if family == "heat_exchanger":
            return (
                unit_node.x + unit_node.width - 40.0 - row * (74.0 if compact_mode else 92.0),
                unit_node.y + unit_node.height + (42.0 if compact_mode else 56.0) + lane * (40.0 if compact_mode else 54.0),
                "bottom",
            )
        return (right_x + lane * (44.0 if compact_mode else 58.0), unit_node.y + 28.0 + row * (72.0 if compact_mode else 90.0), "right")
    if role == "safeguard_relief":
        row, lane = _pid_lite_fan_slot(index, count, per_lane=2)
        if family == "column":
            return (unit_node.x + unit_node.width / 2 + lane * (48.0 if compact_mode else 64.0), unit_node.y - (58.0 if compact_mode else 78.0) - row * (52.0 if compact_mode else 70.0), "top")
        return (right_x + lane * (44.0 if compact_mode else 58.0), top_y - row * (48.0 if compact_mode else 64.0), "top")
    if role == "local_control":
        row, lane = _pid_lite_fan_slot(index, count, per_lane=3)
        spread = 92.0 if compact_mode else 120.0
        items_in_row = min(3, count - lane * 3)
        origin = center_x - ((items_in_row - 1) * spread) / 2
        return (origin + row * spread, top_y - 10.0 - lane * (40.0 if compact_mode else 54.0), "bottom")
    if role == "local_indication":
        row, lane = _pid_lite_fan_slot(index, count, per_lane=3)
        spread = 84.0 if compact_mode else 110.0
        items_in_row = min(3, count - lane * 3)
        origin = center_x - (60.0 if compact_mode else 80.0) - ((items_in_row - 1) * spread) / 2
        return (origin + row * spread, top_y - 2.0 - lane * (38.0 if compact_mode else 50.0), "bottom")
    if role == "process_line":
        row, lane = _pid_lite_fan_slot(index, count, per_lane=3)
        if family == "column":
            return (center_x - (118.0 if compact_mode else 150.0) + row * process_line_step, lower_y + lane * (36.0 if compact_mode else 48.0), "top")
        if family == "heat_exchanger":
            return (center_x - (94.0 if compact_mode else 120.0) + row * process_line_step, lower_y + 8.0 + lane * (36.0 if compact_mode else 48.0), "top")
        return (center_x - (126.0 if compact_mode else 160.0) + row * process_line_step, lower_y + lane * (36.0 if compact_mode else 48.0), "top")
    return (center_x - 96.0 + index * (44.0 if compact_mode else 60.0), center_y - (96.0 if compact_mode else 120.0), "left")


def _pid_lite_fan_slot(index: int, count: int, *, per_lane: int) -> tuple[int, int]:
    del count
    row = index % per_lane
    lane = index // per_lane
    return row, lane


def _build_pid_lite_route_hints(
    sheet_id: str,
    edges: list[DiagramEdge],
    nodes: list[DiagramNode],
    entity_lookup: dict[str, PlantDiagramEntity],
) -> dict[str, dict[str, object]]:
    node_lookup = {node.node_id: node for node in nodes}
    bac_pid_mode = any(entity.metadata.get("bac_pid_profile", "") == "true" for entity in entity_lookup.values())
    route_hints: dict[str, dict[str, object]] = {}
    for edge in edges:
        if edge.sheet_id != sheet_id:
            continue
        source = node_lookup.get(edge.source_node_id)
        target = node_lookup.get(edge.target_node_id)
        if source is None or target is None:
            continue
        source_entity = entity_lookup.get(edge.source_node_id)
        target_entity = entity_lookup.get(edge.target_node_id)
        source_role = source_entity.attachment_role if source_entity is not None else ""
        target_role = target_entity.attachment_role if target_entity is not None else ""

        source_side = _edge_note_value(source.notes, "pid_attach_side") or "right"
        target_side = _edge_note_value(target.notes, "pid_attach_side") or "left"
        corridor_y: float | None = None
        if edge.edge_type == "control_signal":
            source_side = _edge_note_value(source.notes, "pid_attach_side") or ("top" if source.node_family in {"instrument", "controller"} else "right")
            target_side = _edge_note_value(target.notes, "pid_attach_side") or ("top" if target.node_family in {"instrument", "controller"} else "left")
            corridor_y = min(source.y, target.y) - (20.0 if bac_pid_mode else 28.0)
        elif edge.edge_type == "safeguard":
            source_side = _edge_note_value(source.notes, "pid_attach_side") or "top"
            target_side = _edge_note_value(target.notes, "pid_attach_side") or "top"
            corridor_y = min(source.y, target.y) - (26.0 if bac_pid_mode else 36.0)
        elif source_role == "process_line" or target_role == "process_line":
            source_side = _edge_note_value(source.notes, "pid_attach_side") or ("bottom" if source_role == "process_line" else "right")
            target_side = _edge_note_value(target.notes, "pid_attach_side") or ("bottom" if target_role == "process_line" else "left")
            corridor_y = max(source.y + source.height, target.y + target.height) + (16.0 if bac_pid_mode else 24.0)
        elif target_role == "final_control_element":
            source_side = _edge_note_value(source.notes, "pid_attach_side") or "right"
            target_side = _edge_note_value(target.notes, "pid_attach_side") or "left"
            corridor_y = source.y + source.height / 2
        elif source_role == "measurement":
            source_side = _edge_note_value(source.notes, "pid_attach_side") or "right"
            target_side = _edge_note_value(target.notes, "pid_attach_side") or "left"
            corridor_y = source.y + source.height / 2

        start = _node_connection_point(source, source_side)
        end = _node_connection_point(target, target_side)
        if corridor_y is None:
            mid_x = start[0] + max(18.0 if bac_pid_mode else 24.0, (end[0] - start[0]) * (0.40 if bac_pid_mode else 0.45))
            points = [start, (mid_x, start[1]), (mid_x, end[1]), end]
            label_pos = (mid_x, min(start[1], end[1]) - (8.0 if bac_pid_mode else 10.0))
        else:
            points = [start, (start[0], corridor_y), (end[0], corridor_y), end]
            label_pos = ((start[0] + end[0]) / 2, corridor_y - (8.0 if bac_pid_mode else 10.0))
        route_hints[edge.edge_id] = {
            "points": points,
            "label": label_pos,
            "condition": (label_pos[0], label_pos[1] + 14.0),
        }
    return route_hints


def _estimate_pfd_module_footprint(
    module: DiagramModuleSpec,
    semantics: PlantDiagramSemanticsArtifact,
) -> tuple[float, float]:
    entity_lookup = {entity.entity_id: entity for entity in semantics.entities}
    lane_widths: dict[int, float] = {}
    lane_heights: dict[int, float] = {}
    lane_counts: dict[int, int] = {}
    for entity_id in module.entity_ids:
        entity = entity_lookup.get(entity_id)
        if entity is None:
            continue
        unit_type = entity.metadata.get("unit_type", "")
        node = DiagramNode(
            node_id=entity.entity_id,
            label=entity.label,
            node_family=_pfd_node_family(unit_type, entity.label),
            equipment_tag=entity.unit_id or entity.entity_id,
            labels=[DiagramLabel(text=entity.label)],
        )
        _apply_pfd_node_dimensions(node)
        footprint_width, footprint_height = _node_layout_footprint(node)
        lane = _module_lane_index(node)
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        lane_widths[lane] = lane_widths.get(lane, 0.0) + footprint_width
        lane_heights[lane] = max(lane_heights.get(lane, 0.0), footprint_height)
    max_lane_width = 0.0
    for lane, width in lane_widths.items():
        count = lane_counts.get(lane, 1)
        max_lane_width = max(max_lane_width, width + max(0, count - 1) * 36.0)
    active_lanes = sorted(lane_heights)
    total_height = sum(lane_heights.values()) + max(0, len(active_lanes) - 1) * 18.0
    reserved = _module_reserved_margins(module)
    width = max(240.0, max_lane_width + reserved["left"] + reserved["right"] + 40.0)
    height = max(210.0, total_height + reserved["top"] + reserved["bottom"] + 36.0)
    return float(width), float(height)


def _is_bac_target(target: DiagramTargetProfile) -> bool:
    lowered = target.target_product.lower()
    return "benzalkonium" in lowered or "bac" == lowered.strip()


def _bac_pfd_layout_map() -> dict[str, dict[str, object]]:
    return {
        "BAC PFD Panel 1: Feed, Reaction, and Cleanup": {
            "node_positions": {
                "feed_prep": (144.0, 280.0),
                "reactor": (436.0, 214.0),
                "primary_flash": (730.0, 226.0),
                "concentration": (1014.0, 230.0),
            },
            "terminal_positions": {
                "S-101": (42.0, 204.0),
                "S-102": (42.0, 334.0),
            },
            "fallback_origin": (1210.0, 512.0),
            "fallback_step_y": 30.0,
        },
        "BAC PFD Panel 2: Purification, Storage, and Offsites": {
            "node_positions": {
                "purification": (122.0, 198.0),
                "storage": (520.0, 184.0),
                "waste_treatment": (874.0, 184.0),
            },
            "terminal_positions": {
                "S-401": (34.0, 104.0),
                "S-402": (742.0, 122.0),
                "S-404": (730.0, 324.0),
                "S-403": (1098.0, 324.0),
            },
            "fallback_origin": (1102.0, 520.0),
            "fallback_step_y": 30.0,
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


def _apply_bac_single_sheet_pfd_layout(sheet: DiagramSheet, nodes: list[DiagramNode]) -> None:
    layout = {
        "feed_prep": (144.0, 280.0),
        "reactor": (436.0, 214.0),
        "primary_flash": (730.0, 226.0),
        "concentration": (1014.0, 230.0),
        "purification": (122.0, 198.0),
    }
    for node in nodes:
        if node.node_id in layout:
            node.x, node.y = layout[node.node_id]
    sheet.width_px = max(sheet.width_px, 1460)
    sheet.height_px = max(sheet.height_px, 720)


def _pfd_stream_label(stream_id: str, description: str, stream_role: str) -> str:
    if stream_role in {"product", "waste", "vent", "purge", "recycle", "side_draw"}:
        return f"{stream_id}: {stream_role.replace('_', ' ').title()}"
    if description:
        short = description.split(".")[0].strip()
        return f"{stream_id}: {_truncate_with_ellipsis(short, 50)}"
    return stream_id


def _pid_line_class_for_stream(stream) -> str:
    role = (stream.stream_role or "").lower()
    if role == "utility":
        return "utility_service"
    if role == "product":
        return "product_transfer"
    if role in {"waste", "vent", "purge"}:
        return "relief_or_disposal"
    return "process_liquid"


def _pid_line_class_for_variable(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    if any(token in normalized for token in {"steam", "cooling", "chilled", "water", "brine"}):
        return "utility_service"
    if any(token in normalized for token in {"product", "draw", "discharge", "transfer"}):
        return "product_transfer"
    if any(token in normalized for token in {"vent", "purge", "relief"}):
        return "relief_or_disposal"
    return "process_liquid"


def _pid_function_for_actuator(actuator: str) -> str:
    normalized = re.sub(r"\s+", " ", actuator).strip().lower()
    if "valve" in normalized:
        return "control_valve"
    if "pump" in normalized:
        return "pump_speed_control"
    if "heater" in normalized or "steam" in normalized:
        return "heat_input_control"
    return "final_control_element"


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


def _bac_pid_required_unit_ids(flowsheet_graph: FlowsheetGraph) -> list[str]:
    priority_sections = ["reaction", "cleanup", "purification", "storage", "waste_treatment"]
    preferred: list[str] = []
    for section_id in priority_sections:
        for node in flowsheet_graph.nodes:
            if node.section_id == section_id and node.node_id not in preferred:
                preferred.append(node.node_id)
    for node in flowsheet_graph.nodes:
        lowered = f"{node.label} {node.unit_type} {node.section_id}".lower()
        if (
            any(token in lowered for token in {"reactor", "quaternization", "column", "purification", "storage", "tank", "waste", "etp"})
            and node.node_id not in preferred
        ):
            preferred.append(node.node_id)
    return preferred


def _bac_pid_requires_relief(unit_node) -> bool:
    if unit_node is None:
        return False
    lowered = f"{unit_node.label} {unit_node.unit_type} {unit_node.section_id}".lower()
    return any(token in lowered for token in {"reaction", "reactor", "purification", "column", "storage", "tank"})


def _pid_lite_sheet_title(unit_label: str, section_id: str, *, bac_pid_mode: bool) -> str:
    if not bac_pid_mode:
        return f"{unit_label} P&ID-lite Cluster"
    normalized_label = _bac_pid_unit_title_label(unit_label, section_id)
    normalized = (section_id or "").replace("_", " ").strip().lower()
    prefix_map = {
        "reaction": "BAC Reaction P&ID",
        "cleanup": "BAC Cleanup P&ID",
        "purification": "BAC Purification P&ID",
        "storage": "BAC Storage P&ID",
        "waste treatment": "BAC Waste Handling P&ID",
        "waste_treatment": "BAC Waste Handling P&ID",
    }
    prefix = prefix_map.get(normalized)
    if prefix:
        return f"{prefix}: {normalized_label}"
    return f"BAC Local P&ID: {normalized_label}"


def _bac_pid_unit_title_label(unit_label: str, section_id: str) -> str:
    normalized = (section_id or "").replace("_", " ").strip().lower()
    label_map = {
        "reaction": "Reactor",
        "cleanup": "Cleanup Vessel",
        "purification": "Purification Column",
        "storage": "Product Storage",
        "waste treatment": "Waste Handling",
        "waste_treatment": "Waste Handling",
    }
    return label_map.get(normalized, unit_label)


def _display_pid_line_class(line_class: str, *, bac_pid_mode: bool) -> str:
    normalized = line_class.replace("_", " ").title()
    if not bac_pid_mode:
        return normalized
    mapping = {
        "Process Liquid": "BAC Process Liquid",
        "Product Transfer": "BAC Product Transfer",
        "Relief Or Disposal": "BAC Relief / Disposal",
        "Utility Service": "BAC Utility Service",
    }
    return mapping.get(normalized, f"BAC {normalized}")


def _bac_service_label_map() -> dict[str, str]:
    return {
        "M-101": "Feed Prep Vessel",
        "R-101": "Jacketed CSTR",
        "V-101": "Primary Flash Drum",
        "E-101": "Cleanup Exchanger",
        "PU-201": "Purification Column",
        "TK-301": "Product Storage",
        "ETP-401": "Integrated ETP",
        "WT-401": "Integrated ETP",
    }


def _bac_service_label(text: str, equipment_tag: str) -> str:
    return _bac_service_label_map().get(equipment_tag.upper(), text)


def _bac_label_style(node: DiagramNode, label: DiagramLabel, index: int) -> dict[str, object]:
    if label.kind == "primary":
        return {
            "font_size": 14,
            "font_weight": "700",
            "wrap": 12,
            "line_gap": 12,
            "y": node.y + 20,
            "boxed": True,
            "fill": "#ffffff",
            "text": label.text,
        }
    if label.kind == "secondary":
        return {
            "font_size": 10,
            "font_weight": "400",
            "wrap": 18,
            "line_gap": 11,
            "y": node.y + node.height + 14,
            "boxed": False,
            "fill": "#ffffff",
            "text": _bac_service_label(label.text, node.equipment_tag),
        }
    return {
        "font_size": 8,
        "font_weight": "400",
        "wrap": 20,
        "line_gap": 10,
        "y": node.y + node.height + 28 + max(0, index - 2) * 12,
        "boxed": False,
        "fill": "#ffffff",
        "text": label.text,
    }


def _edge_type_from_role(stream_role: str) -> str:
    if stream_role in {"product", "recycle", "purge", "vent", "waste", "side_draw"}:
        return stream_role
    return "main"


def _edge_type_from_diagram_role(role: DiagramEdgeRole) -> str:
    if role == DiagramEdgeRole.PRODUCT:
        return "product"
    if role == DiagramEdgeRole.RECYCLE:
        return "recycle"
    if role == DiagramEdgeRole.PURGE:
        return "purge"
    if role == DiagramEdgeRole.VENT:
        return "vent"
    if role == DiagramEdgeRole.WASTE:
        return "waste"
    if role == DiagramEdgeRole.UTILITY:
        return "utility"
    return "main"


def _edge_note_value(notes: str, key: str) -> str:
    for part in notes.split(";"):
        if "=" not in part:
            continue
        lhs, rhs = part.split("=", 1)
        if lhs.strip() == key:
            return rhs.strip()
    return ""


def _append_note_value(notes: str, key: str, value: str) -> str:
    clean_parts = [part for part in notes.split(";") if part and not part.startswith(f"{key}=")]
    clean_parts.append(f"{key}={value}")
    return ";".join(clean_parts)


def _bac_pfd_route_map() -> dict[str, dict[str, dict[str, object]]]:
    return {
        "BAC PFD Panel 1: Feed, Reaction, and Cleanup": {
            "S-150": {
                "points": [(346.0, 334.0), (390.0, 334.0), (390.0, 304.0), (444.0, 304.0)],
                "label": (392.0, 286.0),
                "condition": (392.0, 300.0),
            },
            "S-201": {
                "points": [(648.0, 304.0), (688.0, 304.0), (688.0, 298.0), (738.0, 298.0)],
                "label": (688.0, 280.0),
                "condition": (688.0, 294.0),
            },
            "S-203": {
                "points": [(922.0, 318.0), (962.0, 318.0), (962.0, 318.0), (1022.0, 318.0)],
                "label": (962.0, 300.0),
                "condition": (962.0, 314.0),
            },
            "S-301": {
                "points": [(1132.0, 304.0), (1180.0, 304.0), (1180.0, 116.0), (210.0, 116.0), (210.0, 334.0)],
                "label": (700.0, 98.0),
                "condition": (700.0, 112.0),
            },
        },
        "BAC PFD Panel 2: Purification, Storage, and Offsites": {
            "S-402": {
                "points": [(358.0, 312.0), (432.0, 312.0), (432.0, 280.0), (528.0, 280.0)],
                "label": (432.0, 262.0),
                "condition": (432.0, 276.0),
            },
            "S-403": {
                "points": [(732.0, 318.0), (792.0, 318.0), (792.0, 314.0), (882.0, 314.0)],
                "label": (792.0, 332.0),
                "condition": (792.0, 346.0),
            },
            "S-404": {
                "points": [(358.0, 246.0), (640.0, 246.0), (640.0, 228.0), (882.0, 228.0)],
                "label": (642.0, 228.0),
                "condition": (642.0, 242.0),
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


def _estimate_label_box(text: str, wrap: int, font_size: int) -> tuple[float, float]:
    lines = _wrap_text_lines(text, wrap)
    if not lines:
        return (0.0, 0.0)
    width = min(300.0, max(78.0, max(len(line) for line in lines) * (font_size * 0.58) + 18.0))
    height = max(20.0, len(lines) * (font_size + 2) + 8.0)
    return (width, height)


def _label_bounds(x: float, baseline_y: float, text: str, wrap: int, font_size: int) -> tuple[float, float, float, float]:
    width, height = _estimate_label_box(text, wrap, font_size)
    return (x - width / 2, baseline_y - 22, width, height)


def _label_bounds_from_style(x: float, baseline_y: float, wrap: int, font_size: int, text: str) -> tuple[float, float, float, float]:
    return _label_bounds(x, baseline_y, text, wrap, font_size)


def _rectangles_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    *,
    padding: float = 0.0,
) -> bool:
    left_x, left_y, left_w, left_h = left
    right_x, right_y, right_w, right_h = right
    return (
        left_x - padding < right_x + right_w
        and right_x - padding < left_x + left_w
        and left_y - padding < right_y + right_h
        and right_y - padding < left_y + left_h
    )


def _segment_intersects_rect(
    start: tuple[float, float],
    end: tuple[float, float],
    rect: tuple[float, float, float, float],
    *,
    padding: float = 0.0,
) -> bool:
    rect_x, rect_y, rect_w, rect_h = rect
    padded = (rect_x - padding, rect_y - padding, rect_w + padding * 2, rect_h + padding * 2)
    x1, y1 = start
    x2, y2 = end
    if abs(x1 - x2) < 0.1:
        seg_y0, seg_y1 = sorted((y1, y2))
        return padded[0] <= x1 <= padded[0] + padded[2] and seg_y0 <= padded[1] + padded[3] and seg_y1 >= padded[1]
    if abs(y1 - y2) < 0.1:
        seg_x0, seg_x1 = sorted((x1, x2))
        return padded[1] <= y1 <= padded[1] + padded[3] and seg_x0 <= padded[0] + padded[2] and seg_x1 >= padded[0]
    seg_left = min(x1, x2)
    seg_top = min(y1, y2)
    seg_rect = (seg_left, seg_top, abs(x2 - x1), abs(y2 - y1))
    return _rectangles_overlap(seg_rect, padded)


def _path_intersects_rect(
    points: list[tuple[float, float]],
    rect: tuple[float, float, float, float],
    *,
    padding: float = 0.0,
) -> bool:
    if len(points) < 2:
        return False
    return any(_segment_intersects_rect(left, right, rect, padding=padding) for left, right in zip(points, points[1:]))


def _clamp_label_position(
    x: float,
    baseline_y: float,
    text: str,
    wrap: int,
    font_size: int,
    sheet: DiagramSheet | None,
) -> tuple[float, float]:
    if sheet is None:
        return (x, baseline_y)
    width, height = _estimate_label_box(text, wrap, font_size)
    min_x = width / 2 + 12
    max_x = sheet.width_px - width / 2 - 12
    min_baseline_y = 24
    max_baseline_y = sheet.height_px - height + 10
    return (
        min(max(x, min_x), max_x),
        min(max(baseline_y, min_baseline_y), max_baseline_y),
    )


def _resolve_edge_label_position(
    x: float,
    baseline_y: float,
    text: str,
    wrap: int,
    font_size: int,
    nodes: list[DiagramNode],
    *,
    sheet: DiagramSheet | None = None,
    route_points: list[tuple[float, float]] | None = None,
    obstacle_rects: list[tuple[float, float, float, float]] | None = None,
) -> tuple[float, float]:
    if not text:
        return (x, baseline_y)
    width, height = _estimate_label_box(text, wrap, font_size)
    base_x, base_y = _clamp_label_position(x, baseline_y, text, wrap, font_size, sheet)
    candidates = [
        (base_x, base_y),
        (base_x, base_y - 30),
        (base_x, base_y + 30 + height * 0.35),
        (base_x - width / 2 - 28, base_y),
        (base_x + width / 2 + 28, base_y),
        (base_x, base_y - 56),
        (base_x, base_y + 56 + height * 0.45),
    ]
    best = (base_x, base_y)
    best_score = float("inf")
    for candidate_x, candidate_y in candidates:
        resolved_x, resolved_y = _clamp_label_position(candidate_x, candidate_y, text, wrap, font_size, sheet)
        label_rect = _label_bounds(resolved_x, resolved_y, text, wrap, font_size)
        overlap_count = 0
        score = abs(resolved_x - base_x) * 0.35 + abs(resolved_y - base_y) * 0.7
        for node in nodes:
            node_rect = (node.x, node.y, node.width, node.height)
            if _rectangles_overlap(label_rect, node_rect, padding=8.0):
                overlap_count += 1
                score += 1000.0
        for obstacle in obstacle_rects or []:
            if _rectangles_overlap(label_rect, obstacle, padding=6.0):
                overlap_count += 1
                score += 1200.0
        if route_points and _path_intersects_rect(route_points, label_rect, padding=4.0):
            score += 420.0
        score += overlap_count * 500.0
        if score < best_score:
            best = (resolved_x, resolved_y)
            best_score = score
            if overlap_count == 0:
                break
    return best


def _node_label_bounds_for_rendering(
    nodes: list[DiagramNode],
    sheet_title: str,
) -> list[tuple[float, float, float, float]]:
    bounds: list[tuple[float, float, float, float]] = []
    for node in nodes:
        for label_style in _node_label_render_styles(node, sheet_title):
            font_size = int(label_style["font_size"])
            wrap_width = int(label_style["wrap"])
            text_y = float(label_style["y"])
            label_text = str(label_style["text"])
            bounds.append(_label_bounds_from_style(node.x + node.width / 2, text_y, wrap_width, font_size, label_text))
    return bounds


def _node_label_render_styles(node: DiagramNode, sheet_title: str) -> list[dict[str, object]]:
    lowered_title = sheet_title.lower()
    if "pfd sheet" in lowered_title or "pfd panel" in lowered_title:
        return [_bac_label_style(node, label, index) for index, label in enumerate(node.labels[:3])]
    if "p&id" in lowered_title and "bac " in lowered_title:
        return _bac_pid_label_styles(node)

    labels = node.labels[:3]
    if not labels:
        return []
    policy = _generic_label_policy(node)
    base_styles: list[dict[str, object]] = []
    for label in labels:
        font_size = 13 if label.kind == "primary" else 10
        font_weight = "700" if label.kind == "primary" else "400"
        wrap_width = policy["primary_wrap"] if label.kind == "primary" else policy["secondary_wrap"]
        line_gap = 12
        if label.kind == "utility":
            font_size = 9
            wrap_width = policy["utility_wrap"]
            line_gap = 11 if policy["compact"] else 12
        base_styles.append(
            {
                "text": label.text,
                "font_size": font_size,
                "font_weight": font_weight,
                "wrap": wrap_width,
                "line_gap": line_gap,
                "boxed": False,
            }
        )

    top_y = node.y + float(policy["top_padding"])
    bottom_y = node.y + max(top_y + 24.0, node.height - float(policy["bottom_padding"]))
    if len(base_styles) == 1:
        single_bias = float(policy["single_bias"])
        y_positions = [min(bottom_y, max(top_y, node.y + node.height * single_bias))]
    else:
        step = max(float(policy["min_step"]), (bottom_y - top_y) / max(1, len(base_styles) - 1))
        y_positions = [top_y + step * index for index in range(len(base_styles))]
        if labels[-1].kind == "utility":
            utility_bias = float(policy["utility_bias"])
            y_positions[-1] = max(y_positions[-1], min(bottom_y, node.y + node.height * utility_bias))

    rendered_styles: list[dict[str, object]] = []
    min_rect_top = node.y + 8.0
    max_rect_bottom = node.y + node.height - 8.0
    label_rects: list[tuple[float, float]] = []
    for style, baseline_y in zip(base_styles, y_positions):
        text = str(style["text"])
        wrap_width = int(style["wrap"])
        font_size = int(style["font_size"])
        height = _estimate_label_box(text, wrap_width, font_size)[1]
        label_rects.append((float(baseline_y) - 22.0, height))

    gap = 2.0
    packed_tops: list[float] = []
    cursor_top = min_rect_top
    for desired_top, height in label_rects:
        top = max(desired_top, cursor_top)
        packed_tops.append(top)
        cursor_top = top + height + gap

    if packed_tops:
        overflow = packed_tops[-1] + label_rects[-1][1] - max_rect_bottom
        if overflow > 0:
            packed_tops = [top - overflow for top in packed_tops]
            packed_tops[0] = max(packed_tops[0], min_rect_top)
            for index in range(1, len(packed_tops)):
                min_top = packed_tops[index - 1] + label_rects[index - 1][1] + gap
                packed_tops[index] = max(packed_tops[index], min_top)
            final_bottom = packed_tops[-1] + label_rects[-1][1]
            if final_bottom > max_rect_bottom:
                packed_tops[-1] = max_rect_bottom - label_rects[-1][1]
                for index in range(len(packed_tops) - 2, -1, -1):
                    max_top = packed_tops[index + 1] - label_rects[index][1] - gap
                    packed_tops[index] = min(packed_tops[index], max_top)
                    packed_tops[index] = max(packed_tops[index], min_rect_top)

    for style, (rect_top, height) in zip(base_styles, zip(packed_tops, [item[1] for item in label_rects])):
        rendered_style = dict(style)
        rendered_style["y"] = rect_top + 22.0
        rendered_styles.append(rendered_style)
    return rendered_styles


def _bac_pid_label_styles(node: DiagramNode) -> list[dict[str, object]]:
    labels = node.labels[:3]
    if not labels:
        return []
    primary = labels[0]
    secondary = labels[1] if len(labels) > 1 else None
    utility = labels[2] if len(labels) > 2 else None

    if node.node_family in {"instrument", "controller", "valve", "relief_valve"}:
        styles: list[dict[str, object]] = [
            {
                "text": primary.text,
                "font_size": 8 if node.node_family in {"instrument", "valve", "relief_valve"} else 9,
                "font_weight": "700",
                "wrap": 10,
                "line_gap": 9,
                "boxed": False,
                "y": node.y + node.height * 0.48,
            }
        ]
        if secondary is not None and node.node_family == "relief_valve":
            styles.append(
                {
                    "text": secondary.text,
                    "font_size": 7,
                    "font_weight": "400",
                    "wrap": 30 if node.node_family == "relief_valve" else 16,
                    "line_gap": 8,
                    "boxed": False,
                    "y": node.y + node.height + 14,
                }
            )
        if utility is not None and node.node_family == "relief_valve":
            styles.append(
                {
                    "text": utility.text,
                    "font_size": 6,
                    "font_weight": "400",
                    "wrap": 14,
                    "line_gap": 7,
                    "boxed": False,
                    "y": node.y + node.height + 26,
                }
            )
        return styles

    styles = [
        {
            "text": primary.text,
            "font_size": 13,
            "font_weight": "700",
            "wrap": 12,
            "line_gap": 11,
            "boxed": False,
            "y": node.y + node.height * 0.32,
        }
    ]
    if secondary is not None:
        styles.append(
            {
                "text": secondary.text,
                "font_size": 7,
                "font_weight": "400",
                "wrap": 16,
                "line_gap": 9,
                "boxed": False,
                "y": node.y - 12,
            }
        )
    if utility is not None and node.node_family == "relief_valve":
        styles.append(
            {
                "text": utility.text,
                "font_size": 7,
                "font_weight": "400",
                "wrap": 16,
                "line_gap": 8,
                "boxed": False,
                "y": node.y + node.height + 16,
            }
        )
    return styles


def _generic_label_policy(node: DiagramNode) -> dict[str, float | int | bool]:
    if node.node_family in {"instrument", "controller", "valve", "relief_valve"}:
        return {
            "top_padding": 12.0,
            "bottom_padding": 10.0,
            "min_step": 12.0,
            "primary_wrap": 10,
            "secondary_wrap": 14,
            "utility_wrap": 12,
            "single_bias": 0.42,
            "utility_bias": 0.74,
            "compact": True,
        }
    if node.node_family == "column":
        return {
            "top_padding": 16.0,
            "bottom_padding": 20.0,
            "min_step": 24.0,
            "primary_wrap": 12,
            "secondary_wrap": 18,
            "utility_wrap": 20,
            "single_bias": 0.24,
            "utility_bias": 0.82,
            "compact": False,
        }
    if node.node_family in {"reactor", "tank", "vessel", "separator"}:
        return {
            "top_padding": 18.0,
            "bottom_padding": 16.0,
            "min_step": 20.0,
            "primary_wrap": 14,
            "secondary_wrap": 20,
            "utility_wrap": 24,
            "single_bias": 0.28,
            "utility_bias": 0.84,
            "compact": False,
        }
    if node.node_family in {"heat exchanger", "condenser"}:
        return {
            "top_padding": 18.0,
            "bottom_padding": 14.0,
            "min_step": 18.0,
            "primary_wrap": 18,
            "secondary_wrap": 22,
            "utility_wrap": 24,
            "single_bias": 0.34,
            "utility_bias": 0.78,
            "compact": True,
        }
    if node.node_family in {"pump", "compressor"}:
        return {
            "top_padding": 16.0,
            "bottom_padding": 10.0,
            "min_step": 14.0,
            "primary_wrap": 14,
            "secondary_wrap": 18,
            "utility_wrap": 20,
            "single_bias": 0.38,
            "utility_bias": 0.74,
            "compact": True,
        }
    return {
        "top_padding": 18.0,
        "bottom_padding": 14.0,
        "min_step": 18.0,
        "primary_wrap": 16,
        "secondary_wrap": 22,
        "utility_wrap": 24,
        "single_bias": 0.32,
        "utility_bias": 0.8,
        "compact": False,
    }


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
    module_placements: list[DiagramModulePlacement] | None = None,
    module_titles: dict[str, str] | None = None,
    continuation_markers: list[dict[str, object]] | None = None,
    route_hints: dict[str, dict[str, object]] | None = None,
) -> str:
    node_lookup = {node.node_id: node for node in nodes}
    node_label_obstacles = _node_label_bounds_for_rendering(nodes, sheet.title)
    edge_label_obstacles = list(node_label_obstacles)
    lowered_title = sheet.title.lower()
    bfd_mode = "block flow diagram" in lowered_title
    pid_lite_mode = "p&id-lite" in lowered_title or "pid-lite" in lowered_title or "p&id" in lowered_title
    pfd_mode = "process flow diagram" in lowered_title or "pfd sheet" in lowered_title or "pfd panel" in lowered_title
    edge_color_map = {
        "main": style.stream_stroke,
        "product": "#2a7f3f",
        "recycle": style.recycle_stroke,
        "purge": "#8a5b2b",
        "vent": "#b36b00",
        "waste": "#a63d40",
        "side_draw": "#6d4c9b",
        "utility": style.utility_stroke,
        "control_signal": "#8b1e3f",
        "safeguard": "#c2410c",
        "continuation": "#475569",
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
    if "pfd sheet" not in lowered_title and "pfd panel" not in lowered_title:
        parts.append(
            f"<text x='{sheet.width_px/2:.0f}' y='34' text-anchor='middle' font-family='{html.escape(style.heading_font_family)}' font-size='22' font-weight='700'>{html.escape(sheet.title)}</text>"
        )
    if subtitle and "pfd sheet" not in lowered_title and "pfd panel" not in lowered_title:
        parts.append(
            f"<text x='{sheet.width_px/2:.0f}' y='58' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='12'>{html.escape(subtitle)}</text>"
        )
    bac_pfd_sheet = ("pfd sheet" in lowered_title or "pfd panel" in lowered_title) and sheet.title.startswith("BAC PFD Panel")
    if "pfd sheet" in lowered_title or "pfd panel" in lowered_title:
        parts.extend(_svg_pfd_sheet_frame(sheet.width_px, sheet.height_px, sheet.title, style))
        parts.extend(_svg_bac_section_zones(sheet))
    if pfd_mode:
        parts.extend(_svg_pfd_legend(sheet.width_px, style))
    if pid_lite_mode:
        parts.extend(_svg_pid_lite_legend(sheet.width_px, nodes, edges, style))
    if module_placements:
        if bac_pfd_sheet:
            parts.extend(_svg_bac_pfd_module_boundaries(module_placements, module_titles or {}, style))
        else:
            parts.extend(_svg_pfd_module_boundaries(module_placements, module_titles or {}, style))

    for edge in edges:
        source = node_lookup.get(edge.source_node_id)
        target = node_lookup.get(edge.target_node_id)
        if source is None or target is None:
            continue
        line_color = edge_color_map.get(edge.edge_type, style.stream_stroke)
        marker = f"url(#arrow-{edge.edge_type if edge.edge_type in edge_color_map else 'main'})"
        stroke_dash = "8,6" if edge.edge_type in {"recycle", "purge", "vent", "waste", "side_draw", "control_signal", "safeguard", "continuation"} else "none"
        lane_note = _edge_note_value(edge.notes, "lane")
        x1, y1 = _node_connection_point(source, "right")
        x2, y2 = _node_connection_point(target, "left")
        route_hint = (route_hints or {}).get(edge.edge_id)
        route_points: list[tuple[float, float]] = []
        manual_route = _bac_edge_route(sheet.title, edge.label) if ("pfd sheet" in lowered_title or "pfd panel" in lowered_title) else None
        if manual_route is not None:
            if "path" in manual_route:
                path = str(manual_route["path"])
                route_points = list(manual_route.get("points", []))
            else:
                route_points = list(manual_route.get("points", []))
                path = _path_from_points(route_points)
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x, label_y = manual_route.get("label", ((x1 + x2) / 2, min(y1, y2) - 8))
            condition_x, condition_y = manual_route.get("condition", (label_x, label_y + 14))
        elif route_hint is not None:
            route_points = list(route_hint.get("points", []))
            path = _path_from_points(route_points)
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x, label_y = route_hint.get("label", ((x1 + x2) / 2, min(y1, y2) - 8))
            condition_x, condition_y = route_hint.get("condition", (label_x, label_y + 14))
        elif edge.edge_type == "recycle":
            mid_y = min(source.y, target.y) - 48
            route_points = [(x1, y1), (x1 + 70.0, mid_y), (x2 - 70.0, mid_y), (x2, y2)]
            path = f"M {x1:.1f} {y1:.1f} C {x1+70:.1f} {mid_y:.1f}, {x2-70:.1f} {mid_y:.1f}, {x2:.1f} {y2:.1f}"
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x = (x1 + x2) / 2
            label_y = mid_y - 10
            condition_x = label_x
            condition_y = label_y + 14
        elif lane_note in {"vent", "waste", "purge"}:
            lane_y = max(source.y + source.height, target.y + target.height) + 34
            route_points = [(x1, y1), (x1, lane_y), (x2, lane_y), (x2, y2)]
            path = f"M {x1:.1f} {y1:.1f} L {x1:.1f} {lane_y:.1f} L {x2:.1f} {lane_y:.1f} L {x2:.1f} {y2:.1f}"
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x = (x1 + x2) / 2
            label_y = lane_y - 10
            condition_x = label_x
            condition_y = label_y + 14
        elif lane_note == "utility":
            lane_y = min(source.y, target.y) - 32
            route_points = [(x1, y1), (x1, lane_y), (x2, lane_y), (x2, y2)]
            path = f"M {x1:.1f} {y1:.1f} L {x1:.1f} {lane_y:.1f} L {x2:.1f} {lane_y:.1f} L {x2:.1f} {y2:.1f}"
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x = (x1 + x2) / 2
            label_y = lane_y - 10
            condition_x = label_x
            condition_y = label_y + 14
        else:
            elbow_x = x1 + max(28.0, (x2 - x1) * 0.45)
            route_points = [(x1, y1), (elbow_x, y1), (elbow_x, y2), (x2, y2)]
            path = f"M {x1:.1f} {y1:.1f} L {elbow_x:.1f} {y1:.1f} L {elbow_x:.1f} {y2:.1f} L {x2:.1f} {y2:.1f}"
            parts.append(
                f"<path d='{path}' fill='none' stroke='{line_color}' stroke-width='2.2' stroke-dasharray='{stroke_dash}' marker-end='{marker}'/>"
            )
            label_x = elbow_x
            label_y = min(y1, y2) - 8
            condition_x = label_x
            condition_y = label_y + 14
        if edge.label and not (bfd_mode and edge.edge_type == "main"):
            label_wrap = 20 if pid_lite_mode else 28
            label_font_size = 10 if pid_lite_mode else 11
            label_x, label_y = _resolve_edge_label_position(
                label_x,
                label_y,
                edge.label,
                label_wrap,
                label_font_size,
                nodes,
                sheet=sheet,
                route_points=route_points,
                obstacle_rects=edge_label_obstacles,
            )
            parts.extend(_svg_label_callout(label_x, label_y - 12, edge.label, style, wrap=label_wrap, font_size=label_font_size))
            parts.append(
                _svg_multiline_text(
                    label_x,
                    label_y,
                    edge.label,
                    style.body_font_family,
                    label_font_size,
                    anchor="middle",
                    wrap=label_wrap,
                    line_gap=11 if pid_lite_mode else 12,
                )
            )
            edge_label_obstacles.append(_label_bounds(label_x, label_y, edge.label, label_wrap, label_font_size))
        if edge.condition_label:
            condition_wrap = 18 if pid_lite_mode else 24
            condition_font_size = 8 if pid_lite_mode else 9
            condition_x, condition_y = _resolve_edge_label_position(
                condition_x,
                condition_y,
                edge.condition_label,
                condition_wrap,
                condition_font_size,
                nodes,
                sheet=sheet,
                route_points=route_points,
                obstacle_rects=edge_label_obstacles,
            )
            parts.extend(
                _svg_label_callout(
                    condition_x,
                    condition_y - 12,
                    edge.condition_label,
                    style,
                    wrap=condition_wrap,
                    font_size=condition_font_size,
                    fill="#fffef8",
                )
            )
            parts.append(
                _svg_multiline_text(
                    condition_x,
                    condition_y,
                    edge.condition_label,
                    style.body_font_family,
                    condition_font_size,
                    anchor="middle",
                    wrap=condition_wrap,
                    line_gap=9 if pid_lite_mode else 10,
                )
            )
            edge_label_obstacles.append(_label_bounds(condition_x, condition_y, edge.condition_label, condition_wrap, condition_font_size))

    for node in nodes:
        parts.extend(_svg_node_shape(node, style))
        for label_style in _node_label_render_styles(node, sheet.title):
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
    if continuation_markers:
        parts.extend(_svg_pfd_continuation_markers(continuation_markers, style))
    if bfd_mode:
        parts.extend(_svg_bfd_clean_frame(sheet.width_px, sheet.height_px, style))
    parts.extend(_svg_drafting_title_block(sheet, style))
    parts.append("</svg>")
    return "".join(parts)


def _svg_drafting_title_block(sheet: DiagramSheet, style: DiagramStyleProfile) -> list[str]:
    width = 430.0
    height = 86.0
    x = max(8.0, sheet.width_px - width - 16.0)
    y = max(8.0, sheet.height_px - height - 14.0)
    rows = [
        ("Drawing", sheet.drawing_number or sheet.sheet_id),
        ("Sheet", sheet.sheet_number or sheet.sheet_id),
        ("Rev", sheet.revision or "A"),
        ("Status", sheet.issue_status or "For Review"),
        ("Date", sheet.revision_date or utc_now()[:10]),
        ("By", sheet.prepared_by or "AoC"),
    ]
    parts = [
        f"<g class='drafting-title-block'>",
        f"<rect x='{x:.1f}' y='{y:.1f}' width='{width:.1f}' height='{height:.1f}' fill='#ffffff' stroke='#111827' stroke-width='1.0'/>",
        f"<line x1='{x:.1f}' y1='{y + 24:.1f}' x2='{x + width:.1f}' y2='{y + 24:.1f}' stroke='#111827' stroke-width='1.0'/>",
        f"<text x='{x + 10:.1f}' y='{y + 17:.1f}' font-family='{html.escape(style.heading_font_family)}' font-size='11' font-weight='700'>DRAFTING TITLE BLOCK</text>",
    ]
    col_width = width / 3
    for index, (label, value) in enumerate(rows):
        col = index % 3
        row = index // 3
        cell_x = x + col * col_width
        cell_y = y + 24.0 + row * 31.0
        parts.append(f"<rect x='{cell_x:.1f}' y='{cell_y:.1f}' width='{col_width:.1f}' height='31.0' fill='none' stroke='#d1d5db' stroke-width='0.8'/>")
        parts.append(f"<text x='{cell_x + 6:.1f}' y='{cell_y + 11:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='7.5' fill='#475569'>{html.escape(label)}</text>")
        parts.append(f"<text x='{cell_x + 6:.1f}' y='{cell_y + 24:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='9.2' font-weight='700'>{html.escape(value)}</text>")
    parts.append("</g>")
    return parts


def _svg_bfd_clean_frame(width_px: int, height_px: int, style: DiagramStyleProfile) -> list[str]:
    return [
        f"<rect x='34' y='86' width='{width_px - 68:.1f}' height='{height_px - 204:.1f}' fill='none' stroke='#d6dde6' stroke-width='0.9'/>",
        f"<line x1='34' y1='118' x2='{width_px - 34:.1f}' y2='118' stroke='#d6dde6' stroke-width='0.9'/>",
        f"<text x='48' y='108' font-family='{html.escape(style.body_font_family)}' font-size='10.2' font-weight='700'>BAC SECTION SPINE</text>",
    ]


def _build_instrumented_overlay_sheet(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    style: DiagramStyleProfile,
    *,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
    routing: DiagramRoutingArtifact | None = None,
) -> DiagramSheet:
    nodes, edges = _build_control_overlay_nodes_and_edges(
        control_plan,
        control_architecture,
        style,
        modules=modules,
        sheet_composition=sheet_composition,
    )
    overlay_composition = next((sheet for sheet in sheet_composition.sheets if sheet.sheet_id == "sheet_2"), None) if sheet_composition is not None else None
    if routing is not None:
        routing_sheet = next((item for item in routing.sheets if item.sheet_id == "sheet_2"), None)
        route_hints = {
            hint.edge_id: {
                "points": [(point.x, point.y) for point in hint.points],
                "label": (hint.label_x, hint.label_y),
                "condition": (hint.condition_x, hint.condition_y),
            }
            for hint in (routing_sheet.route_hints if routing_sheet is not None else [])
        }
    else:
        route_hints = _build_control_overlay_route_hints(edges, nodes)
    overlay_svg = _render_svg(
        DiagramSheet(
            sheet_id="sheet_2",
            title="Instrumented Process Flow Overlay",
            width_px=overlay_composition.width_px if overlay_composition is not None else max(style.canvas_width_px, int(len(nodes) * 250 + 240)),
            height_px=overlay_composition.height_px if overlay_composition is not None else max(style.canvas_height_px, 940),
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
        route_hints=route_hints,
    )
    return DiagramSheet(
        sheet_id="sheet_2",
        title="Instrumented Process Flow Overlay",
        width_px=overlay_composition.width_px if overlay_composition is not None else max(style.canvas_width_px, int(len(nodes) * 250 + 240)),
        height_px=overlay_composition.height_px if overlay_composition is not None else max(style.canvas_height_px, 940),
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


def _build_control_overlay_nodes_and_edges(
    control_plan: ControlPlanArtifact,
    control_architecture: ControlArchitectureDecision,
    style: DiagramStyleProfile,
    *,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
) -> tuple[list[DiagramNode], list[DiagramEdge]]:
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
    overlay_composition = next((sheet for sheet in sheet_composition.sheets if sheet.sheet_id == "sheet_2"), None) if sheet_composition is not None else None
    if modules is not None and overlay_composition is not None:
        module_lookup = {module.module_id: module for module in modules.modules}
        placement_lookup = {placement.module_id: placement for placement in overlay_composition.module_placements}
        for unit_id in ordered_unit_ids:
            node = next((item for item in nodes if item.node_id == unit_id), None)
            if node is None:
                continue
            module_id = next((module.module_id for module in modules.modules if unit_id in module.unit_ids), "")
            placement = placement_lookup.get(module_id)
            if placement is None:
                continue
            _apply_pfd_node_dimensions(node)
            node.x = placement.x + max(18.0, (placement.width - node.width) / 2)
            node.y = placement.y + max(20.0, (placement.height - node.height) / 2)
    else:
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
    return nodes, edges


def _build_control_overlay_route_hints(
    edges: list[DiagramEdge],
    nodes: list[DiagramNode],
) -> dict[str, dict[str, object]]:
    node_lookup = {node.node_id: node for node in nodes}
    route_hints: dict[str, dict[str, object]] = {}
    for edge in edges:
        source_node = node_lookup.get(edge.source_node_id)
        target_node = node_lookup.get(edge.target_node_id)
        if source_node is None or target_node is None:
            continue
        points = _best_module_route(
            source_node,
            target_node,
            DiagramModulePlacement(
                module_id="control_overlay",
                sheet_id=edge.sheet_id,
                x=min(source_node.x, target_node.x) - 80.0,
                y=min(source_node.y, target_node.y) - 120.0,
                width=abs(target_node.x - source_node.x) + 320.0,
                height=max(source_node.height, target_node.height) + 260.0,
            ),
            "right",
            "left",
        )
        label_anchor_index = max(1, min(len(points) - 2, len(points) // 2))
        label_point = points[label_anchor_index]
        route_hints[edge.edge_id] = {
            "points": points,
            "label": (label_point[0], label_point[1] - 12.0),
            "condition": (label_point[0], label_point[1] + 2.0),
        }
    return _optimize_pfd_route_hints(route_hints, 2200, 1200)


def _build_control_interlock_sheet(
    control_plan: ControlPlanArtifact,
    flowsheet_graph: FlowsheetGraph,
    style: DiagramStyleProfile,
    *,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
) -> DiagramSheet:
    unit_label_by_id = {node.node_id: node.label for node in flowsheet_graph.nodes}
    unit_to_loops: dict[str, list[ControlLoop]] = {}
    for loop in control_plan.control_loops:
        if loop.unit_id:
            unit_to_loops.setdefault(loop.unit_id, []).append(loop)
    interlock_composition = next((sheet for sheet in sheet_composition.sheets if sheet.sheet_id == "sheet_3"), None) if sheet_composition is not None else None
    width_px = interlock_composition.width_px if interlock_composition is not None else max(style.canvas_width_px, 1760)
    height_px = interlock_composition.height_px if interlock_composition is not None else max(style.canvas_height_px, 980)
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width_px}' height='{height_px}' viewBox='0 0 {width_px} {height_px}'>",
        f"<rect x='1' y='1' width='{width_px - 2}' height='{height_px - 2}' fill='white' stroke='#222' stroke-width='1.2'/>",
        f"<text x='{width_px/2:.0f}' y='34' text-anchor='middle' font-family='{html.escape(style.heading_font_family)}' font-size='22' font-weight='700'>Interlocks and Permissives</text>",
        f"<text x='{width_px/2:.0f}' y='58' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='12'>Startup permissives, shutdown actions, overrides, and safeguard linkages for principal loop clusters</text>",
    ]
    placement_lookup = {placement.module_id: placement for placement in interlock_composition.module_placements} if interlock_composition is not None else {}
    if interlock_composition is not None:
        module_titles = {module.module_id: module.title for module in modules.modules} if modules is not None else {}
        parts.extend(_svg_pfd_module_boundaries(interlock_composition.module_placements, module_titles, style))
    if modules is None:
        ordered_modules: list[tuple[str, str, list[ControlLoop], DiagramModulePlacement | None]] = []
    else:
        ordered_modules = []
        for module in modules.modules:
            unit_id = next((item for item in module.unit_ids if item), "")
            loops = unit_to_loops.get(unit_id, [])
            if not loops:
                continue
            ordered_modules.append((module.module_id, unit_id, loops, placement_lookup.get(module.module_id)))

    for module_id, unit_id, loops, placement in ordered_modules[:6]:
        px = placement.x if placement is not None else 120.0
        py = placement.y if placement is not None else 140.0
        pw = placement.width if placement is not None else 640.0
        unit_label = _display_equipment_label(unit_label_by_id.get(unit_id) or unit_id)
        parts.append(f"<text x='{px + 18:.1f}' y='{py + 22:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='12' font-weight='700'>{html.escape(unit_label)} ({html.escape(unit_id)})</text>")
        header_y = py + 40.0
        col1_x = px + 32.0
        col2_x = px + 158.0
        col3_x = px + 322.0
        col4_x = px + 468.0
        col5_x = px + 586.0
        parts.append(f"<text x='{col1_x:.1f}' y='{header_y:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='9.5' font-weight='700'>Loop</text>")
        parts.append(f"<text x='{col2_x:.1f}' y='{header_y:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='9.5' font-weight='700'>Cause / permissive</text>")
        parts.append(f"<text x='{col3_x:.1f}' y='{header_y:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='9.5' font-weight='700'>Action / shutdown</text>")
        parts.append(f"<text x='{col4_x:.1f}' y='{header_y:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='9.5' font-weight='700'>Override</text>")
        parts.append(f"<text x='{col5_x:.1f}' y='{header_y:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='9.5' font-weight='700'>Safeguard / trip</text>")
        parts.append(f"<line x1='{px + 16:.1f}' y1='{header_y + 8:.1f}' x2='{px + pw - 16:.1f}' y2='{header_y + 8:.1f}' stroke='#cbd5e1' stroke-width='0.9'/>")
        row_y = py + 52.0
        for loop in loops[:3]:
            critical_fill = "#fff1f2" if (loop.criticality or "").lower() == "high" else "#f8fafc"
            critical_stroke = "#a63d40" if (loop.criticality or "").lower() == "high" else "#94a3b8"
            parts.append(
                f"<rect x='{px + 16:.1f}' y='{row_y:.1f}' width='{pw - 32:.1f}' height='64' rx='10' ry='10' fill='{critical_fill}' stroke='{critical_stroke}' stroke-width='1.1'/>"
            )
            parts.append(_svg_multiline_text(col1_x, row_y + 22.0, loop.control_id, style.body_font_family, 11, anchor="start", font_weight="700", wrap=14, line_gap=10))
            parts.append(_svg_multiline_text(col1_x, row_y + 40.0, loop.controlled_variable, style.body_font_family, 8, anchor="start", wrap=16, line_gap=9))
            parts.append(_svg_multiline_text(col2_x, row_y + 18.0, loop.startup_logic or "Standard startup permissive", style.body_font_family, 8.6, anchor="start", wrap=18, line_gap=9))
            parts.append(_svg_multiline_text(col2_x, row_y + 40.0, loop.controlled_variable or "Process condition", style.body_font_family, 8.0, anchor="start", wrap=18, line_gap=9))
            parts.append(_svg_multiline_text(col3_x, row_y + 18.0, loop.shutdown_logic or "Standard shutdown rundown", style.body_font_family, 8.6, anchor="start", wrap=16, line_gap=9))
            parts.append(_svg_multiline_text(col3_x, row_y + 40.0, loop.manipulated_variable or "Control action", style.body_font_family, 8.0, anchor="start", wrap=16, line_gap=9))
            parts.append(_svg_multiline_text(col4_x, row_y + 18.0, loop.override_logic or "Basic operator override", style.body_font_family, 8.6, anchor="start", wrap=12, line_gap=9))
            parts.append(_svg_multiline_text(col4_x, row_y + 40.0, f"Criticality: {(loop.criticality or 'medium').title()}", style.body_font_family, 8.0, anchor="start", wrap=12, line_gap=9))
            parts.append(_svg_multiline_text(col5_x, row_y + 18.0, loop.safeguard_linkage or "No dedicated trip linkage", style.body_font_family, 8.6, anchor="start", wrap=12, line_gap=9))
            parts.append(_svg_multiline_text(col5_x, row_y + 40.0, "Protective trip / interlock" if loop.safeguard_linkage else "Monitoring only", style.body_font_family, 8.0, anchor="start", wrap=12, line_gap=9))
            row_y += 74.0
    parts.append("</svg>")
    return DiagramSheet(
        sheet_id="sheet_3",
        title="Interlocks and Permissives",
        width_px=width_px,
        height_px=height_px,
        orientation="landscape",
        presentation_mode="sheet",
        preferred_scale=1.0,
        full_page=True,
        legend_mode="embedded",
        suppress_inline_wrapping=True,
        svg="".join(parts),
    )


def _build_control_shutdown_sheet(
    control_plan: ControlPlanArtifact,
    flowsheet_graph: FlowsheetGraph,
    style: DiagramStyleProfile,
    *,
    modules: DiagramModuleArtifact | None = None,
    sheet_composition: DiagramSheetCompositionArtifact | None = None,
) -> DiagramSheet:
    unit_label_by_id = {node.node_id: node.label for node in flowsheet_graph.nodes}
    unit_to_loops: dict[str, list[ControlLoop]] = {}
    for loop in control_plan.control_loops:
        if loop.unit_id and (loop.safeguard_linkage or loop.shutdown_logic or (loop.criticality or "").lower() == "high"):
            unit_to_loops.setdefault(loop.unit_id, []).append(loop)
    shutdown_composition = next((sheet for sheet in sheet_composition.sheets if sheet.sheet_id == "sheet_4"), None) if sheet_composition is not None else None
    width_px = shutdown_composition.width_px if shutdown_composition is not None else max(style.canvas_width_px, 1760)
    height_px = shutdown_composition.height_px if shutdown_composition is not None else max(style.canvas_height_px, 920)
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width_px}' height='{height_px}' viewBox='0 0 {width_px} {height_px}'>",
        f"<rect x='1' y='1' width='{width_px - 2}' height='{height_px - 2}' fill='white' stroke='#222' stroke-width='1.2'/>",
        f"<text x='{width_px/2:.0f}' y='34' text-anchor='middle' font-family='{html.escape(style.heading_font_family)}' font-size='22' font-weight='700'>Shutdowns and Protective Trips</text>",
        f"<text x='{width_px/2:.0f}' y='58' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='12'>Focused review sheet for safety-critical shutdown actions, trip causes, and protected final actions</text>",
    ]
    placement_lookup = {placement.module_id: placement for placement in shutdown_composition.module_placements} if shutdown_composition is not None else {}
    if shutdown_composition is not None and modules is not None:
        module_titles = {module.module_id: module.title for module in modules.modules}
        parts.extend(_svg_pfd_module_boundaries(shutdown_composition.module_placements, module_titles, style))
    ordered_modules: list[tuple[str, str, list[ControlLoop], DiagramModulePlacement | None]] = []
    if modules is not None:
        for module in modules.modules:
            unit_id = next((item for item in module.unit_ids if item), "")
            loops = unit_to_loops.get(unit_id, [])
            if loops:
                ordered_modules.append((module.module_id, unit_id, loops, placement_lookup.get(module.module_id)))
    for module_id, unit_id, loops, placement in ordered_modules[:6]:
        px = placement.x if placement is not None else 120.0
        py = placement.y if placement is not None else 140.0
        pw = placement.width if placement is not None else 640.0
        unit_label = _display_equipment_label(unit_label_by_id.get(unit_id) or unit_id)
        parts.append(f"<text x='{px + 18:.1f}' y='{py + 22:.1f}' font-family='{html.escape(style.body_font_family)}' font-size='12' font-weight='700'>{html.escape(unit_label)} ({html.escape(unit_id)})</text>")
        row_y = py + 34.0
        for loop in loops[:2]:
            parts.append(
                f"<rect x='{px + 16:.1f}' y='{row_y:.1f}' width='{pw - 32:.1f}' height='58' rx='10' ry='10' fill='#fff1f2' stroke='#a63d40' stroke-width='1.1'/>"
            )
            parts.append(_svg_multiline_text(px + 32.0, row_y + 18.0, loop.control_id, style.body_font_family, 11, anchor="start", font_weight="700", wrap=14, line_gap=10))
            parts.append(_svg_multiline_text(px + 150.0, row_y + 16.0, f"Trip cause: {loop.safeguard_linkage or loop.controlled_variable}", style.body_font_family, 8.8, anchor="start", wrap=34, line_gap=9))
            parts.append(_svg_multiline_text(px + 150.0, row_y + 31.0, f"Shutdown action: {loop.shutdown_logic or 'Standard shutdown rundown'}", style.body_font_family, 8.8, anchor="start", wrap=34, line_gap=9))
            parts.append(_svg_multiline_text(px + 150.0, row_y + 46.0, f"Protected final action: {loop.manipulated_variable or loop.actuator or 'Protective action'}", style.body_font_family, 8.4, anchor="start", wrap=34, line_gap=9))
            row_y += 68.0
    parts.append("</svg>")
    return DiagramSheet(
        sheet_id="sheet_4",
        title="Shutdowns and Protective Trips",
        width_px=width_px,
        height_px=height_px,
        orientation="landscape",
        presentation_mode="sheet",
        preferred_scale=1.0,
        full_page=True,
        legend_mode="embedded",
        suppress_inline_wrapping=True,
        svg="".join(parts),
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
    module_placements: list[DiagramModulePlacement] | None = None,
    module_titles: dict[str, str] | None = None,
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
    placement_by_unit: dict[str, DiagramModulePlacement] = {}
    if module_placements:
        for unit_id, placement in zip(unit_ids, sorted(module_placements, key=lambda item: item.z_index)):
            placement_by_unit[unit_id] = placement
        parts.extend(_svg_pfd_module_boundaries(module_placements, module_titles or {}, style))
    for index, unit_id in enumerate(unit_ids):
        loops = loop_groups.get(unit_id, [])
        placement = placement_by_unit.get(unit_id)
        if placement is not None:
            x_center = placement.x + placement.width / 2
            unit_width = min(190.0, placement.width - 32.0)
            unit_x = x_center - unit_width / 2
            local_unit_y = placement.y + 24.0
            local_loop_y = local_unit_y + 96.0
        else:
            x_center = x_margin + spacing * index + spacing / 2
            unit_width = min(190, spacing - 24)
            unit_x = x_center - unit_width / 2
            local_unit_y = unit_y
            local_loop_y = loop_y
        unit_label = _display_equipment_label(unit_label_by_id.get(unit_id) or unit_id)
        parts.append(
            f"<rect x='{unit_x:.1f}' y='{local_unit_y:.1f}' width='{unit_width:.1f}' height='72' rx='8' ry='8' fill='#f7f7f7' stroke='{style.node_stroke}' stroke-width='1.5'/>"
        )
        parts.append(_svg_multiline_text(x_center, local_unit_y + 24, unit_label, style.body_font_family, 12, anchor="middle", font_weight="700", wrap=18, line_gap=12))
        parts.append(_svg_multiline_text(x_center, local_unit_y + 49, unit_id, style.body_font_family, 10, anchor="middle", wrap=20, line_gap=11))
        loop_box_y = local_loop_y
        for loop in loops[:4]:
            critical_color = "#a63d40" if (loop.criticality or "").lower() == "high" else "#456b9a"
            parts.append(
                f"<line x1='{x_center:.1f}' y1='{local_unit_y + 72:.1f}' x2='{x_center:.1f}' y2='{loop_box_y:.1f}' stroke='#7b8794' stroke-width='1.2'/>"
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


def _ordered_control_units_from_composition(
    modules: DiagramModuleArtifact,
    composition: DiagramSheetCompositionArtifact,
) -> list[str]:
    module_lookup = {module.module_id: module for module in modules.modules}
    architecture_sheet = next((sheet for sheet in composition.sheets if sheet.sheet_id == "sheet_1"), None)
    if architecture_sheet is None:
        return []
    ordered_unit_ids: list[str] = []
    for placement in sorted(architecture_sheet.module_placements, key=lambda item: item.z_index):
        module = module_lookup.get(placement.module_id)
        if module is None:
            continue
        for unit_id in module.unit_ids:
            if unit_id and unit_id not in ordered_unit_ids:
                ordered_unit_ids.append(unit_id)
    return ordered_unit_ids


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


def _template_port_geometry(
    node: DiagramNode,
    side: str,
    port_role: str,
) -> tuple[float, float] | None:
    family = (_edge_note_value(node.notes, "template_family") or "").strip().lower()
    if not family:
        family = {
            "heat exchanger": "heat_exchanger",
            "separator": "vessel",
        }.get(node.node_family, node.node_family.replace(" ", "_"))
    if not family:
        return None
    role = port_role.strip().lower()
    if not role:
        return None
    templates = build_diagram_equipment_templates()
    template = _template_for_family(family, templates)
    if template is not None:
        template_port = next((port for port in template.ports if port.port_role == role), None)
        if template_port is not None and template_port.side.value != side:
            return None
    x_ratio = 1.0 if side == "right" else 0.0 if side == "left" else 0.5
    y_ratio = 0.5 if side in {"left", "right"} else 0.0 if side == "top" else 1.0
    if family == "column":
        if role == "overhead":
            x_ratio, y_ratio = 0.5, 0.02
        elif role == "bottoms":
            x_ratio, y_ratio = 0.5, 0.98
        elif role == "process_inlet":
            x_ratio, y_ratio = 0.0, 0.35
        elif role == "process_outlet":
            x_ratio, y_ratio = 1.0, 0.35
    elif family in {"reactor", "vessel", "tank"}:
        if role in {"measurement", "process_inlet"}:
            x_ratio, y_ratio = 0.0, 0.4 if family == "reactor" else 0.45
        elif role == "process_outlet":
            x_ratio, y_ratio = 1.0, 0.55 if family == "reactor" else 0.5
        elif role in {"safeguard", "vent"}:
            x_ratio, y_ratio = 0.5, 0.02
        elif role == "drain":
            x_ratio, y_ratio = 0.5, 0.98
    elif family == "heat_exchanger":
        if role == "process_inlet":
            x_ratio, y_ratio = 0.0, 0.5
        elif role == "process_outlet":
            x_ratio, y_ratio = 1.0, 0.5
        elif role == "utility_inlet":
            x_ratio, y_ratio = 0.68, 0.0
        elif role == "utility_outlet":
            x_ratio, y_ratio = 0.32, 1.0
    elif family in {"pump", "terminal"}:
        if role == "process_inlet":
            x_ratio, y_ratio = 0.0, 0.58 if family == "pump" else 0.5
        elif role == "process_outlet":
            x_ratio, y_ratio = 1.0, 0.58 if family == "pump" else 0.5
    else:
        return None
    return (node.x + node.width * x_ratio, node.y + node.height * y_ratio)


def _template_port_side_for_node(node: DiagramNode | None, port_role: str) -> str:
    if node is None or not port_role:
        return ""
    family = (_edge_note_value(node.notes, "template_family") or "").strip().lower()
    if not family:
        family = {
            "heat exchanger": "heat_exchanger",
            "separator": "vessel",
        }.get(node.node_family, node.node_family.replace(" ", "_"))
    template = _template_for_family(family, build_diagram_equipment_templates())
    if template is None:
        return ""
    port = next((item for item in template.ports if item.port_role == port_role), None)
    return port.side.value if port is not None else ""


def _node_connection_point(node: DiagramNode, side: str, port_role: str = "") -> tuple[float, float]:
    forced_side = _edge_note_value(node.notes, "pid_attach_side")
    if forced_side:
        side = forced_side
    template_point = _template_port_geometry(node, side, port_role)
    if template_point is not None:
        return template_point
    cx = node.x + node.width / 2
    cy = node.y + node.height / 2
    if side == "top":
        return (cx, node.y)
    if side == "bottom":
        return (cx, node.y + node.height)
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
    template_family = (_edge_note_value(node.notes, "template_family") or "").strip().lower()

    def template_overlays() -> list[str]:
        overlays: list[str] = []
        if template_family == "column":
            cx = x + w / 2
            overlays.extend(
                [
                    f"<line x1='{cx:.1f}' y1='{y - 12:.1f}' x2='{cx:.1f}' y2='{y + 6:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
                    f"<circle cx='{cx:.1f}' cy='{y - 14:.1f}' r='4.0' fill='white' stroke='{stroke}' stroke-width='1.0'/>",
                    f"<line x1='{cx:.1f}' y1='{y + h - 6:.1f}' x2='{cx:.1f}' y2='{y + h + 12:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
                    f"<circle cx='{cx:.1f}' cy='{y + h + 14:.1f}' r='4.0' fill='white' stroke='{stroke}' stroke-width='1.0'/>",
                ]
            )
        elif template_family == "heat_exchanger":
            top_x = x + w * 0.68
            bottom_x = x + w * 0.32
            overlays.extend(
                [
                    f"<line x1='{top_x:.1f}' y1='{y - 10:.1f}' x2='{top_x:.1f}' y2='{y + 10:.1f}' stroke='#4a6fa5' stroke-width='1.2'/>",
                    f"<circle cx='{top_x:.1f}' cy='{y - 12:.1f}' r='3.6' fill='white' stroke='#4a6fa5' stroke-width='1.0'/>",
                    f"<line x1='{bottom_x:.1f}' y1='{y + h - 10:.1f}' x2='{bottom_x:.1f}' y2='{y + h + 10:.1f}' stroke='#4a6fa5' stroke-width='1.2'/>",
                    f"<circle cx='{bottom_x:.1f}' cy='{y + h + 12:.1f}' r='3.6' fill='white' stroke='#4a6fa5' stroke-width='1.0'/>",
                ]
            )
        elif template_family == "reactor":
            cx = x + w / 2
            overlays.extend(
                [
                    f"<line x1='{cx + 18:.1f}' y1='{y - 10:.1f}' x2='{cx + 18:.1f}' y2='{y + 8:.1f}' stroke='#c2410c' stroke-width='1.2'/>",
                    f"<circle cx='{cx + 18:.1f}' cy='{y - 12:.1f}' r='3.8' fill='white' stroke='#c2410c' stroke-width='1.0'/>",
                ]
            )
        elif template_family in {"vessel", "tank"}:
            cx = x + w / 2
            overlays.extend(
                [
                    f"<line x1='{cx:.1f}' y1='{y - 10:.1f}' x2='{cx:.1f}' y2='{y + 8:.1f}' stroke='{stroke}' stroke-width='1.1'/>",
                    f"<circle cx='{cx:.1f}' cy='{y - 12:.1f}' r='3.6' fill='white' stroke='{stroke}' stroke-width='1.0'/>",
                ]
            )
        return overlays

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
        ] + template_overlays()
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
        ] + template_overlays()
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
        ] + template_overlays()
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
    if node.node_family in {"vessel", "tank"}:
        return [
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + 16:.1f}' rx='{(w - 32)/2:.1f}' ry='16' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<rect x='{x + 16:.1f}' y='{y + 16:.1f}' width='{w - 32:.1f}' height='{h - 32:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<ellipse cx='{x + w/2:.1f}' cy='{y + h - 16:.1f}' rx='{(w - 32)/2:.1f}' ry='16' fill='{fill}' stroke='{stroke}' stroke-width='1.6'/>",
            f"<line x1='{x + 8:.1f}' y1='{cy:.1f}' x2='{x + 18:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
            f"<line x1='{x + w - 18:.1f}' y1='{cy:.1f}' x2='{x + w - 8:.1f}' y2='{cy:.1f}' stroke='{stroke}' stroke-width='1.2'/>",
        ] + template_overlays()
    if node.node_family == "instrument":
        return [
            f"<circle cx='{x + w/2:.1f}' cy='{y + h/2:.1f}' r='{min(w, h)/2 - 6:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + h - 6:.1f}' x2='{x + w/2:.1f}' y2='{y + h + 20:.1f}' stroke='{stroke}' stroke-width='1.1'/>",
        ]
    if node.node_family == "controller":
        return [
            f"<polygon points='{x + w/2:.1f},{y + 6:.1f} {x + w - 6:.1f},{y + h/2:.1f} {x + w/2:.1f},{y + h - 6:.1f} {x + 6:.1f},{y + h/2:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>"
        ]
    if node.node_family == "relief_valve":
        return [
            f"<polygon points='{x + 8:.1f},{y + h/2:.1f} {x + w/2:.1f},{y + 10:.1f} {x + w - 8:.1f},{y + h/2:.1f} {x + w/2:.1f},{y + h - 10:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
            f"<line x1='{x + w/2:.1f}' y1='{y + 10:.1f}' x2='{x + w/2:.1f}' y2='{y - 10:.1f}' stroke='{stroke}' stroke-width='1.1'/>",
        ]
    if node.node_family == "valve":
        return [
            f"<polygon points='{x + 8:.1f},{y + h/2:.1f} {x + w/2:.1f},{y + 10:.1f} {x + w - 8:.1f},{y + h/2:.1f} {x + w/2:.1f},{y + h - 10:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>"
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
    x = max(80, width_px - 286)
    y = 126
    items = [
        ("Main process stream", style.stream_stroke, "none"),
        ("Product stream", "#2a7f3f", "none"),
        ("Vent / purge / waste", "#a63d40", "8,6"),
        ("Recycle stream", style.recycle_stroke, "8,6"),
    ]
    parts = [
        f"<rect x='{x}' y='{y}' width='240' height='112' rx='0' ry='0' fill='#fdfefe' stroke='#56606b' stroke-width='0.9'/>",
        f"<line x1='{x}' y1='{y + 22}' x2='{x + 240}' y2='{y + 22}' stroke='#56606b' stroke-width='0.9'/>",
        f"<text x='{x + 120}' y='{y + 16}' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='9.8' font-weight='700'>LEGEND AND NOTATION</text>",
    ]
    for index, (label, color, dash) in enumerate(items):
        y0 = y + 42 + index * 18
        dash_attr = f" stroke-dasharray='{dash}'" if dash != "none" else ""
        parts.append(f"<line x1='{x + 16}' y1='{y0}' x2='{x + 62}' y2='{y0}' stroke='{color}' stroke-width='2.4'{dash_attr}/>")
        parts.append(f"<text x='{x + 72}' y='{y0 + 4}' font-family='{html.escape(style.body_font_family)}' font-size='9.4'>{html.escape(label)}</text>")
    parts.append(f"<text x='{x + 16}' y='{y + 98}' font-family='{html.escape(style.body_font_family)}' font-size='8.4'>Tags above symbols, services below symbols</text>")
    parts.append(f"<text x='{x + 16}' y='{y + 108}' font-family='{html.escape(style.body_font_family)}' font-size='8.4'>Major lines labeled by stream number</text>")
    return parts


def _svg_pid_lite_legend(
    width_px: int,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    style: DiagramStyleProfile,
) -> list[str]:
    x = max(920, width_px - 302)
    y = 104
    line_classes: list[str] = []
    for edge in edges:
        if edge.condition_label and edge.condition_label not in line_classes:
            line_classes.append(edge.condition_label)
    line_classes = line_classes[:3]

    loop_tags: list[str] = []
    for node in nodes:
        for label in node.labels:
            if label.kind == "utility" and label.text and label.text not in loop_tags:
                loop_tags.append(label.text)
    loop_tags = loop_tags[:4]

    symbol_entries: list[str] = []
    family_labels = [
        ("instrument", "Instrument bubble"),
        ("controller", "Local controller"),
        ("valve", "Valve / final element"),
        ("relief_valve", "Relief valve"),
        ("reactor", "Unit anchor"),
        ("column", "Unit anchor"),
        ("vessel", "Unit anchor"),
        ("separator", "Unit anchor"),
        ("tank", "Unit anchor"),
        ("heat exchanger", "Unit anchor"),
    ]
    node_families = {node.node_family for node in nodes}
    for family, label in family_labels:
        if family in node_families and label not in symbol_entries:
            symbol_entries.append(label)
    symbol_entries = symbol_entries[:4]

    box_height = 98 + max(len(line_classes), 1) * 11 + max(len(loop_tags), 1) * 11 + max(len(symbol_entries), 1) * 11
    parts = [
        f"<rect x='{x}' y='{y}' width='236' height='{box_height}' rx='0' ry='0' fill='#fdfefe' stroke='#56606b' stroke-width='1.0'/>",
        f"<line x1='{x}' y1='{y + 22}' x2='{x + 236}' y2='{y + 22}' stroke='#56606b' stroke-width='1.0'/>",
        f"<text x='{x + 118}' y='{y + 16}' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='10.2' font-weight='700'>P&amp;ID-LITE LEGEND</text>",
    ]
    cursor_y = y + 38
    parts.append(f"<text x='{x + 12}' y='{cursor_y}' font-family='{html.escape(style.body_font_family)}' font-size='9.6' font-weight='700'>Line Classes</text>")
    cursor_y += 13
    for item in line_classes or ["See inline line tags"]:
        parts.append(f"<text x='{x + 12}' y='{cursor_y}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>{html.escape(item)}</text>")
        cursor_y += 11
    parts.append(f"<text x='{x + 12}' y='{cursor_y + 3}' font-family='{html.escape(style.body_font_family)}' font-size='9.6' font-weight='700'>Loop Tags</text>")
    cursor_y += 16
    for item in loop_tags or ["Local loop IDs shown on bubbles"]:
        parts.append(f"<text x='{x + 12}' y='{cursor_y}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>{html.escape(item)}</text>")
        cursor_y += 11
    parts.append(f"<text x='{x + 12}' y='{cursor_y + 3}' font-family='{html.escape(style.body_font_family)}' font-size='9.6' font-weight='700'>Symbols</text>")
    cursor_y += 16
    for item in symbol_entries or ["Unit anchor", "Instrument bubble", "Valve / final element"]:
        parts.append(f"<text x='{x + 12}' y='{cursor_y}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>{html.escape(item)}</text>")
        cursor_y += 11
    return parts


def _svg_pfd_module_boundaries(
    module_placements: list[DiagramModulePlacement],
    module_titles: dict[str, str],
    style: DiagramStyleProfile,
) -> list[str]:
    parts: list[str] = []
    for placement in module_placements:
        title = module_titles.get(placement.module_id, placement.module_id.replace("_", " ").title())
        parts.append(
            f"<rect x='{placement.x:.1f}' y='{placement.y:.1f}' width='{placement.width:.1f}' height='{placement.height:.1f}' "
            "rx='10' ry='10' fill='none' stroke='#cbd5e1' stroke-width='1.0' stroke-dasharray='8,6'/>"
        )
        parts.append(
            f"<rect x='{placement.x + 12:.1f}' y='{placement.y - 16:.1f}' width='156' height='22' rx='8' ry='8' fill='#ffffff' stroke='#cbd5e1' stroke-width='0.8'/>"
        )
        parts.append(
            _svg_multiline_text(
                placement.x + 20.0,
                placement.y - 1.0,
                title,
                style.body_font_family,
                9.5,
                anchor="start",
                font_weight="700",
                wrap=24,
                line_gap=10,
            )
        )
    return parts


def _svg_bac_pfd_module_boundaries(
    module_placements: list[DiagramModulePlacement],
    module_titles: dict[str, str],
    style: DiagramStyleProfile,
) -> list[str]:
    parts: list[str] = []
    for placement in module_placements:
        title = module_titles.get(placement.module_id, placement.module_id.replace("_", " ").title())
        parts.append(
            f"<rect x='{placement.x:.1f}' y='{placement.y:.1f}' width='{placement.width:.1f}' height='{placement.height:.1f}' "
            "rx='10' ry='10' fill='none' stroke='#d5dde7' stroke-width='0.8' stroke-dasharray='7,6'/>"
        )
        parts.append(
            f"<rect x='{placement.x + 10:.1f}' y='{placement.y - 14:.1f}' width='146' height='20' rx='7' ry='7' fill='#f7fafc' stroke='#d5dde7' stroke-width='0.7'/>"
        )
        parts.append(
            _svg_multiline_text(
                placement.x + 18.0,
                placement.y,
                title,
                style.body_font_family,
                9,
                anchor="start",
                font_weight="700",
                wrap=24,
                line_gap=9,
            )
        )
    return parts


def _svg_pfd_continuation_markers(markers: list[dict[str, object]], style: DiagramStyleProfile) -> list[str]:
    parts: list[str] = []
    for marker in markers:
        x = float(marker.get("x", 0.0))
        y = float(marker.get("y", 0.0))
        side = str(marker.get("side", "right"))
        label = str(marker.get("label", "Continuation"))
        target_sheet = str(marker.get("target_sheet", "next sheet"))
        arrow = "&gt;&gt;" if side == "right" else "&lt;&lt;"
        box_x = x - 66 if side == "left" else x - 6
        parts.append(
            f"<rect x='{box_x:.1f}' y='{y - 14:.1f}' width='72' height='28' rx='10' ry='10' fill='#fff7ed' stroke='#fb923c' stroke-width='1.0'/>"
        )
        parts.append(
            f"<text x='{x:.1f}' y='{y + 4:.1f}' text-anchor='middle' font-family='{html.escape(style.body_font_family)}' font-size='14' font-weight='700' fill='#c2410c'>{arrow}</text>"
        )
        parts.append(
            _svg_multiline_text(
                x + (56.0 if side == "right" else -56.0),
                y - 2.0,
                f"{label} -> {target_sheet}" if side == "right" else f"{target_sheet} <- {label}",
                style.body_font_family,
                9,
                anchor="start" if side == "right" else "end",
                font_weight="700",
                wrap=22,
                line_gap=10,
            )
        )
    return parts


def _svg_pfd_sheet_frame(width_px: int, height_px: int, title: str, style: DiagramStyleProfile) -> list[str]:
    title_x = 52
    title_y = 42
    frame_x = 38
    frame_y = 38
    frame_w = width_px - 76
    frame_h = height_px - 76
    title_band_h = 46
    info_x = width_px - 384
    info_y = height_px - 118
    parts = [
        f"<rect x='{frame_x}' y='{frame_y}' width='{frame_w}' height='{frame_h}' fill='none' stroke='#222' stroke-width='1.0'/>",
        f"<rect x='{frame_x + 10}' y='{frame_y + 10}' width='{frame_w - 20}' height='{frame_h - 20}' fill='none' stroke='#7f8a96' stroke-width='0.8'/>",
        f"<rect x='{frame_x + 10}' y='{frame_y + 10}' width='{frame_w - 20}' height='{title_band_h}' fill='#f7f9fc' stroke='#7f8a96' stroke-width='0.8'/>",
        f"<line x1='{frame_x + 10}' y1='{frame_y + 10 + title_band_h}' x2='{frame_x + frame_w - 10}' y2='{frame_y + 10 + title_band_h}' stroke='#7f8a96' stroke-width='0.8'/>",
        f"<rect x='{frame_x + 22}' y='{frame_y + 78}' width='{frame_w - 44}' height='{frame_h - 186}' fill='none' stroke='#d8dde5' stroke-width='0.7'/>",
        f"<text x='{title_x}' y='{title_y}' font-family='{html.escape(style.heading_font_family)}' font-size='15.5' font-weight='700'>PROCESS FLOW DIAGRAM</text>",
        f"<text x='{title_x}' y='{title_y + 18}' font-family='{html.escape(style.body_font_family)}' font-size='10.8'>{html.escape(title)}</text>",
        f"<text x='{title_x + 470}' y='{title_y}' font-family='{html.escape(style.body_font_family)}' font-size='9.8' font-weight='700'>Project: Benzalkonium Chloride</text>",
        f"<text x='{title_x + 470}' y='{title_y + 18}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>Landscape process sheet with orthogonal stream routing</text>",
        f"<rect x='{info_x}' y='{info_y}' width='336' height='78' rx='0' ry='0' fill='#ffffff' stroke='#222' stroke-width='1.0'/>",
        f"<line x1='{info_x}' y1='{info_y + 24}' x2='{info_x + 336}' y2='{info_y + 24}' stroke='#222' stroke-width='1.0'/>",
        f"<text x='{info_x + 12}' y='{info_y + 16}' font-family='{html.escape(style.body_font_family)}' font-size='10' font-weight='700'>DRAWING NOTES</text>",
        f"<text x='{info_x + 12}' y='{info_y + 41}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>1. Process representation only</text>",
        f"<text x='{info_x + 12}' y='{info_y + 55}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>2. Major streams labeled by stream number</text>",
        f"<text x='{info_x + 12}' y='{info_y + 69}' font-family='{html.escape(style.body_font_family)}' font-size='8.8'>3. Tags above equipment, services below</text>",
    ]
    return parts


def _svg_bac_section_zones(sheet: DiagramSheet) -> list[str]:
    del sheet
    return []


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
    width, height = _estimate_label_box(text, wrap, font_size)
    if width <= 0 or height <= 0:
        return []
    return [
        f"<rect x='{x - width/2:.1f}' y='{y - 10:.1f}' width='{width:.1f}' height='{height:.1f}' rx='4' ry='4' fill='{fill}' stroke='#d0d7de' stroke-width='0.8'/>"
    ]
