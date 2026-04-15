from pathlib import Path
import unittest

from aoc.diagrams import (
    apply_diagram_drafting_metadata,
    apply_diagram_review_workflow_metadata,
    build_bac_drawing_package_artifact,
    build_block_flow_diagram,
    build_bac_diagram_benchmark_artifact,
    build_bac_rendering_audit_artifact,
    build_diagram_acceptance,
    build_diagram_domain_packs,
    build_diagram_equipment_templates,
    build_domain_equipment_templates,
    build_drawio_document,
    _apply_pfd_node_dimensions,
    _layout_module_nodes,
    _module_reserved_margins,
    _node_connection_point,
    _node_label_bounds_for_rendering,
    _node_label_render_styles,
    _node_layout_footprint,
    _pfd_route_points_within_module,
    _path_intersects_rect,
    _build_pfd_sheet_route_hints,
    _build_pfd_connector_lane_reservations,
    _build_pid_lite_route_hints,
    _optimize_pfd_route_hints,
    _routing_quality_metrics,
    _label_bounds,
    _rectangles_overlap,
    _resolve_edge_label_position,
    _render_svg,
    _svg_node_shape,
    build_block_flow_diagram_modules,
    build_block_flow_diagram_semantics,
    build_block_flow_diagram_sheet_composition,
    build_control_cause_effect_artifact,
    build_control_system_diagram,
    build_control_system_modules,
    build_control_system_routing_artifact,
    build_control_system_semantics,
    build_control_system_sheet_composition,
    build_diagram_style_profile,
    build_diagram_symbol_library,
    build_diagram_target_profile,
    build_pid_lite_diagram,
    build_pid_lite_modules,
    build_pid_lite_routing_artifact,
    build_pid_lite_semantics,
    build_pid_lite_sheet_composition,
    build_process_flow_diagram,
    build_process_flow_diagram_modules,
    build_process_flow_diagram_routing_artifact,
    build_process_flow_diagram_semantics,
    build_process_flow_diagram_sheet_composition,
)
from aoc.models import BACDiagramBenchmarkArtifact, BACRenderingAuditArtifact, BlockFlowDiagramArtifact, ControlArchitectureDecision, ControlLoop, ControlPlanArtifact, DecisionRecord, DiagramAcceptanceArtifact, DiagramLabel, DiagramNode, DiagramRoutingArtifact, DiagramRoutingSheet, DiagramSheet, DiagramSheetComposition, EnergyBalance, FlowsheetBlueprintArtifact, FlowsheetBlueprintStep, FlowsheetCase, FlowsheetGraph, FlowsheetNode, PidLiteDiagramArtifact, ProcessFlowDiagramArtifact, ProjectBasis, RecycleLoop, RecycleIntentArtifact, StreamComponentFlow, StreamRecord, StreamSpec, StreamTable, UnitDuty
from aoc.models import DiagramEdge, DiagramEdgeRole, DiagramEntityKind, DiagramLevel, DiagramInterModuleConnector, DiagramModuleArtifact, DiagramModulePlacement, DiagramModulePort, DiagramModuleSpec, DiagramPortSide, DiagramRoutingArtifact, DiagramRoutingSheet, DiagramSheetCompositionArtifact, DiagramSymbolPolicy
from aoc.validators import (
    validate_diagram_module_artifact,
    validate_diagram_module_symbols_against_library,
    validate_diagram_semantics_against_symbol_library,
    validate_plant_diagram_semantics,
)


class DiagramArchitectureTests(unittest.TestCase):
    def _fixture_path(self, name: str) -> Path:
        return Path(__file__).parent / "fixtures" / name

    def _pfd_svg_regression_signature(self, artifact) -> str:
        sheet = artifact.sheets[0]
        svg = sheet.svg
        module_boundary_count = svg.count("stroke='#cbd5e1' stroke-width='1.0' stroke-dasharray='8,6'")
        label_callout_count = svg.count("stroke='#d0d7de'")
        main_arrow_count = svg.count("marker-end='url(#arrow-main)'")
        lines = [
            f"sheet_count={len(artifact.sheets)}",
            f"sheet_width={sheet.width_px}",
            f"sheet_height={sheet.height_px}",
            f"module_boundary_count={module_boundary_count}",
            f"label_callout_count={label_callout_count}",
            f"main_arrow_count={main_arrow_count}",
            f"has_feed_handling={int('Feed_Handling' in svg)}",
            f"has_reaction={int('Reaction' in svg)}",
            f"has_purification={int('Purification' in svg)}",
            f"has_s2_label={int('S2: To reactor' in svg)}",
            f"has_s3_label={int('S3: To column' in svg)}",
            f"has_s2_condition={int('40 C / 2.0 bar' in svg)}",
            f"has_s3_condition={int('80 C / 2.5 bar' in svg)}",
        ]
        return "\n".join(lines) + "\n"

    def _drawio_regression_signature(self, drawio: str) -> str:
        module_box_count = drawio.count("dashPattern=8 6")
        vertex_count = drawio.count('vertex="1"')
        title_block_count = drawio.count("DRAFTING TITLE BLOCK")
        lines = [
            f"page_count={drawio.count('<diagram ')}",
            f"module_box_count={module_box_count}",
            f"edge_count={drawio.count('edgeStyle=orthogonalEdgeStyle')}",
            f"node_count={vertex_count - module_box_count - title_block_count}",
            f"has_feed_handling={int('Feed Handling' in drawio)}",
            f"has_reaction={int('Reaction' in drawio)}",
            f"has_purification={int('Purification' in drawio)}",
            f"has_to_reactor={int('To reactor' in drawio)}",
            f"has_to_column={int('To column' in drawio)}",
        ]
        return "\n".join(lines) + "\n"

    def _pid_svg_regression_signature(self, artifact) -> str:
        sheet = artifact.sheets[0]
        svg = sheet.svg
        lines = [
            f"title={sheet.title}",
            f"has_bac_title={int('BAC ' in sheet.title)}",
            f"has_bac_process_liquid={int('BAC Process Liquid' in svg)}",
            f"has_bac_relief={int('BAC Relief / Disposal' in svg or 'BAC Relief' in svg)}",
            f"has_title_block={int('DRAFTING TITLE BLOCK' in svg)}",
            f"has_pid_legend={int('P&amp;ID-LITE LEGEND' in svg)}",
        ]
        return "\n".join(lines) + "\n"

    def _pid_multi_sheet_signature(self, artifact) -> str:
        titles = [sheet.title for sheet in artifact.sheets]
        panel_titles = [sheet.stitch_panel_title for sheet in artifact.sheets]
        combined_svg = "\n".join(sheet.svg for sheet in artifact.sheets)
        lines = [
            f"sheet_count={len(artifact.sheets)}",
            f"titles={' | '.join(titles)}",
            f"panel_titles={' | '.join(panel_titles)}",
            f"has_purification_title={int(any('BAC Purification P&ID: Purification Column' == title for title in titles))}",
            f"has_storage_title={int(any('BAC Storage P&ID: Product Storage' == title for title in titles))}",
            f"has_reactor_title={int(any('BAC Reaction P&ID: Reactor' == title for title in titles))}",
            f"has_relief_wording={int('Pressure Relief Valve' in combined_svg or 'Relief Valve' in combined_svg)}",
            f"has_psv_tag={int('PSV-' in combined_svg)}",
            f"has_bac_product_transfer={int('BAC Product Transfer' in combined_svg)}",
            f"has_panel_marker={int('BAC P&amp;ID Panel' in combined_svg)}",
        ]
        return "\n".join(lines) + "\n"

    def _bac_bfd_svg_signature(self, artifact) -> str:
        sheet = artifact.sheets[0]
        svg = sheet.svg
        section_labels = [node.labels[0].text for node in artifact.nodes[:7]]
        section_text = " | ".join(section_labels)
        main_flow_count = svg.count("marker-end='url(#arrow-main)'")
        recycle_count = svg.count("marker-end='url(#arrow-recycle)'")
        lines = [
            f"title={sheet.title}",
            f"section_count={len(artifact.nodes)}",
            f"main_flow_count={main_flow_count}",
            f"recycle_count={recycle_count}",
            f"has_title_block={int('DRAFTING TITLE BLOCK' in svg)}",
            f"has_quaternization={int('Quaternization Reaction' in section_text)}",
            f"has_product_storage={int('Product Storage' in section_text)}",
            f"section_labels={' | '.join(section_labels)}",
        ]
        return "\n".join(lines) + "\n"

    def _bac_pfd_svg_signature(self, artifact) -> str:
        titles = [sheet.title for sheet in artifact.sheets]
        combined_svg = "\n".join(sheet.svg for sheet in artifact.sheets)
        lines = [
            f"sheet_count={len(artifact.sheets)}",
            f"titles={' | '.join(titles)}",
            f"has_panel1_title={int('BAC PFD Panel 1: Feed, Reaction, and Cleanup' in titles)}",
            f"has_panel2_title={int('BAC PFD Panel 2: Purification, Storage, and Offsites' in titles)}",
            f"has_reactor={int('Jacketed CSTR' in combined_svg and 'R-101' in combined_svg)}",
            f"has_purification={int('Purification' in combined_svg and 'PU-201' in combined_svg)}",
            f"has_storage={int('Product Storage' in combined_svg)}",
            f"has_s150={int('S-150: Reactor feed' in combined_svg)}",
            f"has_s201={int('S-201: Reactor effluent' in combined_svg)}",
            f"has_s402={int('S-402: Product' in combined_svg)}",
            f"has_panel_marker={int('Panel 2: Purification,' in combined_svg)}",
            f"has_title_block={sum('DRAFTING TITLE BLOCK' in sheet.svg for sheet in artifact.sheets)}",
            f"has_pfd_legend={sum('LEGEND AND NOTATION' in sheet.svg for sheet in artifact.sheets)}",
        ]
        return "\n".join(lines) + "\n"

    def _bac_drawio_signature(self, drawio: str) -> str:
        has_equipment_layer = 'id="layer_equipment"' in drawio
        has_streams_layer = 'id="layer_streams"' in drawio
        has_annotations_layer = 'id="layer_annotations"' in drawio
        has_stable_node_id = 'id="n_sheet_1_reactor"' in drawio
        has_stable_edge_id = 'id="e_sheet_1_pfd_edge_' in drawio
        lines = [
            f"page_count={drawio.count('<diagram ')}",
            f"has_equipment_layer={int(has_equipment_layer)}",
            f"has_streams_layer={int(has_streams_layer)}",
            f"has_annotations_layer={int(has_annotations_layer)}",
            f"has_bac_panel_1={int('BAC PFD Panel 1: Feed, Reaction, and Cleanup' in drawio)}",
            f"has_bac_panel_2={int('BAC PFD Panel 2: Purification, Storage, and Offsites' in drawio)}",
            f"has_stitch_to_sheet2={int('Continues to: sheet_2' in drawio)}",
            f"has_stitch_from_sheet1={int('Continues from: sheet_1' in drawio)}",
            f"has_stable_node_id={int(has_stable_node_id)}",
            f"has_stable_edge_id={int(has_stable_edge_id)}",
        ]
        return "\n".join(lines) + "\n"

    def _build_bac_pfd_regression_artifact(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pfd_fixture",
            route_id="route_bac_pfd_fixture",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed Preparation", section_id="feed"),
                FlowsheetNode(node_id="reactor", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="primary_flash", unit_type="flash_vessel", label="Primary Flash", section_id="cleanup"),
                FlowsheetNode(node_id="concentration", unit_type="heat_exchanger", label="Concentration", section_id="concentration"),
                FlowsheetNode(node_id="purification", unit_type="distillation_column", label="Purification", section_id="purification"),
                FlowsheetNode(node_id="storage", unit_type="tank", label="Storage", section_id="storage"),
                FlowsheetNode(node_id="waste_treatment", unit_type="waste_treatment", label="Waste Treatment", section_id="waste_treatment"),
            ],
            unit_models=[],
            section_ids=["feed", "reaction", "cleanup", "concentration", "purification", "storage", "waste_treatment"],
            stream_ids=["S-101", "S-102", "S-150", "S-201", "S-202", "S-203", "S-401", "S-402", "S-403", "S-404"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_records = [
            StreamRecord(stream_id="S-101", description="Fresh BAC feed", temperature_c=25.0, pressure_bar=1.0, components=[], destination_unit_id="feed_prep", stream_role="feed", section_id="feed"),
            StreamRecord(stream_id="S-102", description="Diluent feed", temperature_c=25.0, pressure_bar=1.0, components=[], destination_unit_id="feed_prep", stream_role="feed", section_id="feed"),
            StreamRecord(stream_id="S-150", description="Reactor feed", temperature_c=45.0, pressure_bar=2.0, components=[], source_unit_id="feed_prep", destination_unit_id="reactor", stream_role="intermediate", section_id="reaction"),
            StreamRecord(stream_id="S-201", description="Reactor effluent", temperature_c=85.0, pressure_bar=3.1, components=[], source_unit_id="reactor", destination_unit_id="primary_flash", stream_role="intermediate", section_id="cleanup"),
            StreamRecord(stream_id="S-202", description="Vent purge", temperature_c=55.0, pressure_bar=1.2, components=[], source_unit_id="primary_flash", destination_unit_id="waste_treatment", stream_role="vent", section_id="cleanup"),
            StreamRecord(stream_id="S-203", description="Rich liquid to cleanup", temperature_c=70.0, pressure_bar=2.4, components=[], source_unit_id="primary_flash", destination_unit_id="concentration", stream_role="intermediate", section_id="cleanup"),
            StreamRecord(stream_id="S-401", description="Recycle return", temperature_c=40.0, pressure_bar=1.4, components=[], source_unit_id="purification", stream_role="recycle", section_id="purification"),
            StreamRecord(stream_id="S-402", description="Product to storage", temperature_c=35.0, pressure_bar=1.1, components=[], source_unit_id="purification", destination_unit_id="storage", stream_role="product", section_id="purification"),
            StreamRecord(stream_id="S-403", description="Waste to ETP", temperature_c=32.0, pressure_bar=1.0, components=[], source_unit_id="storage", destination_unit_id="waste_treatment", stream_role="waste", section_id="storage"),
            StreamRecord(stream_id="S-404", description="Side draw", temperature_c=48.0, pressure_bar=1.3, components=[], source_unit_id="purification", destination_unit_id="waste_treatment", stream_role="side_draw", section_id="purification"),
        ]
        stream_table = StreamTable(
            streams=stream_records,
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_bac_pfd_fixture",
            route_id="route_bac_pfd_fixture",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id=record.stream_id, source_unit_id=record.source_unit_id, destination_unit_id=record.destination_unit_id, stream_role=record.stream_role, section_id=record.section_id)
                for record in stream_records
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
        )
        return artifact

    def _build_phase4_regression_artifact(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_regression",
            route_id="route_regression",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="TK-101", unit_type="tank", label="Feed Tank", section_id="feed_handling"),
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="C-101", unit_type="distillation_column", label="Column", section_id="purification"),
            ],
            unit_models=[],
            section_ids=["feed_handling", "reaction", "purification"],
            stream_ids=["S1", "S2", "S3"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Fresh feed",
                    temperature_c=25.0,
                    pressure_bar=1.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="TK-101",
                    stream_role="feed",
                    section_id="feed_handling",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="To reactor",
                    temperature_c=40.0,
                    pressure_bar=2.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="TK-101",
                    destination_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S3",
                    description="To column",
                    temperature_c=80.0,
                    pressure_bar=2.5,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=9.0, molar_flow_kmol_hr=0.09)],
                    source_unit_id="R-101",
                    destination_unit_id="C-101",
                    stream_role="intermediate",
                    section_id="purification",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_regression",
            route_id="route_regression",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamSpec(stream_id="S2", source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
                StreamSpec(stream_id="S3", source_unit_id="R-101", destination_unit_id="C-101", stream_role="intermediate", section_id="purification"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )
        return artifact, flowsheet_graph, flowsheet_case, stream_table, library, style, target, modules, composition

    def _make_blueprint(self) -> FlowsheetBlueprintArtifact:
        return FlowsheetBlueprintArtifact(
            blueprint_id="bp_1",
            route_id="route_1",
            route_name="Demo Route",
            steps=[
                FlowsheetBlueprintStep(
                    step_id="feed",
                    route_id="route_1",
                    section_id="feed_handling",
                    section_label="Feed handling",
                    step_role="feed_preparation",
                    unit_id="feed_prep",
                    unit_type="feed_preparation",
                    service="Feed preparation",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                FlowsheetBlueprintStep(
                    step_id="rxn",
                    route_id="route_1",
                    section_id="reaction",
                    section_label="Reaction",
                    step_role="reaction",
                    unit_id="reactor",
                    unit_type="cstr",
                    service="Reaction",
                    upstream_step_ids=["feed"],
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                FlowsheetBlueprintStep(
                    step_id="pur",
                    route_id="route_1",
                    section_id="purification",
                    section_label="Purification",
                    step_role="purification",
                    unit_id="column",
                    unit_type="distillation",
                    service="Purification",
                    upstream_step_ids=["rxn"],
                    citations=["s1"],
                    assumptions=["seed"],
                ),
            ],
            recycle_intents=[
                RecycleIntentArtifact(
                    intent_id="r1",
                    route_id="route_1",
                    source_step_id="pur",
                    target_step_id="rxn",
                    stream_family="mother_liquor",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            citations=["s1"],
            assumptions=["seed"],
            markdown="seed",
        )

    def _build_pfd_acceptance_for_case(
        self,
        *,
        case_id: str,
        section_nodes: list[tuple[str, str, str, str]],
        stream_specs: list[tuple[str, str, str, str, float, float]],
    ):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id=f"fg_{case_id}",
            route_id=f"route_{case_id}",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id=node_id, unit_type=unit_type, label=label, section_id=section_id)
                for node_id, unit_type, label, section_id in section_nodes
            ],
            unit_models=[],
            section_ids=list(dict.fromkeys(section_id for _, _, _, section_id in section_nodes)),
            stream_ids=[stream_id for stream_id, *_ in stream_specs],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id=stream_id,
                    description=description,
                    temperature_c=temperature_c,
                    pressure_bar=pressure_bar,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id=source_unit_id or None,
                    destination_unit_id=destination_unit_id or None,
                    stream_role="feed" if not source_unit_id else "intermediate",
                    section_id=destination_section,
                )
                for stream_id, description, source_unit_id, destination_unit_id, temperature_c, pressure_bar, destination_section in [
                    (stream_id, description, source_unit_id, destination_unit_id, temperature_c, pressure_bar, next((section for node_id, _, _, section in section_nodes if node_id == (destination_unit_id or source_unit_id)), "process"))
                    for stream_id, description, source_unit_id, destination_unit_id, temperature_c, pressure_bar in stream_specs
                ]
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id=f"case_{case_id}",
            route_id=f"route_{case_id}",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(
                    stream_id=stream_id,
                    source_unit_id=source_unit_id or None,
                    destination_unit_id=destination_unit_id or None,
                    stream_role="feed" if not source_unit_id else "intermediate",
                    section_id=next((section for node_id, _, _, section in section_nodes if node_id == (destination_unit_id or source_unit_id)), "process"),
                )
                for stream_id, _, source_unit_id, destination_unit_id, _, _ in stream_specs
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )
        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id=artifact.diagram_id,
            nodes=artifact.nodes,
            edges=artifact.edges,
            sheets=artifact.sheets,
            modules=modules,
            sheet_composition=composition,
            target=target,
            flowsheet_graph=flowsheet_graph,
            flowsheet_case=flowsheet_case,
        )
        return acceptance, composition, artifact, modules

    def test_bfd_phase3_builders_emit_semantics_modules_and_composition(self):
        blueprint = self._make_blueprint()
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()

        semantics = build_block_flow_diagram_semantics(blueprint, target, library)
        modules = build_block_flow_diagram_modules(semantics, library)
        composition = build_block_flow_diagram_sheet_composition(modules, semantics, style, library)

        self.assertEqual(len(semantics.entities), 3)
        self.assertEqual(len(modules.modules), 3)
        self.assertEqual(len(composition.sheets), 1)
        self.assertEqual(len(composition.sheets[0].module_placements), 3)
        self.assertTrue(any(connection.role.value == "recycle" for connection in semantics.connections))

    def test_pfd_phase3_builders_emit_semantics_modules_and_composition(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_1",
            route_id="route_1",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="TK-101", unit_type="tank", label="Feed Tank", section_id="feed_handling"),
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="C-101", unit_type="distillation_column", label="Column", section_id="purification"),
            ],
            unit_models=[],
            section_ids=["feed_handling", "reaction", "purification"],
            stream_ids=["S1", "S2", "S3"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Fresh feed",
                    temperature_c=25.0,
                    pressure_bar=1.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="TK-101",
                    stream_role="feed",
                    section_id="feed_handling",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="To reactor",
                    temperature_c=40.0,
                    pressure_bar=2.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="TK-101",
                    destination_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S3",
                    description="To column",
                    temperature_c=80.0,
                    pressure_bar=2.5,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=9.0, molar_flow_kmol_hr=0.09)],
                    source_unit_id="R-101",
                    destination_unit_id="C-101",
                    stream_role="intermediate",
                    section_id="purification",
                ),
                StreamRecord(
                    stream_id="S4",
                    description="Product",
                    temperature_c=30.0,
                    pressure_bar=1.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=8.5, molar_flow_kmol_hr=0.085)],
                    source_unit_id="C-101",
                    stream_role="product",
                    section_id="purification",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_1",
            route_id="route_1",
            operating_mode="continuous",
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamSpec(stream_id="S2", source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
                StreamSpec(stream_id="S3", source_unit_id="R-101", destination_unit_id="C-101", stream_role="intermediate", section_id="purification"),
                StreamSpec(stream_id="S4", source_unit_id="C-101", stream_role="product", section_id="purification"),
            ],
            units=[],
            sections=[],
            separations=[],
            composition_states=[],
            composition_closures=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            recycle_loops=[RecycleLoop(loop_id="L1", recycle_stream_ids=["S5"], recycle_source_unit_id="C-101", recycle_target_unit_id="R-101", convergence_status="estimated", citations=["s1"], assumptions=["seed"])],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)

        self.assertGreaterEqual(len(semantics.entities), 4)
        self.assertEqual(len(modules.modules), 3)
        self.assertGreaterEqual(len(composition.sheets), 1)
        self.assertTrue(any(connection.role.value == "recycle" for connection in semantics.connections))

    def test_pfd_renderer_uses_sheet_composition_artifact(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        target.main_body_max_pfd_nodes = 1
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_2",
            route_id="route_2",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="TK-101", unit_type="tank", label="Feed Tank", section_id="feed_handling"),
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["feed_handling", "reaction"],
            stream_ids=["S1", "S2"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Feed",
                    temperature_c=25.0,
                    pressure_bar=1.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="TK-101",
                    stream_role="feed",
                    section_id="feed_handling",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="Transfer",
                    temperature_c=40.0,
                    pressure_bar=2.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="TK-101",
                    destination_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_2",
            route_id="route_2",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamSpec(stream_id="S2", source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)

        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )

        self.assertEqual(len(artifact.sheets), 2)
        self.assertEqual(artifact.sheets[0].title, "Process Flow Diagram")
        self.assertEqual(artifact.sheets[1].title, "PFD Sheet 2")

    def test_pfd_renderer_draws_module_boundaries_and_continuation_markers(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        target.main_body_max_pfd_nodes = 1
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_3",
            route_id="route_3",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="TK-101", unit_type="tank", label="Feed Tank", section_id="feed_handling"),
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["feed_handling", "reaction"],
            stream_ids=["S1", "S2"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Feed",
                    temperature_c=25.0,
                    pressure_bar=1.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="TK-101",
                    stream_role="feed",
                    section_id="feed_handling",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="Transfer",
                    temperature_c=40.0,
                    pressure_bar=2.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="TK-101",
                    destination_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_3",
            route_id="route_3",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamSpec(stream_id="S2", source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)

        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )

        self.assertIn("stroke-dasharray='8,6'", artifact.sheets[0].svg)
        self.assertIn("feed_handling", artifact.sheets[0].svg.lower())
        self.assertIn("sheet_2", artifact.sheets[0].svg)

    def test_pfd_renderer_draws_module_boundaries_and_continuations(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        target.main_body_max_pfd_nodes = 1
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_3",
            route_id="route_3",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="TK-101", unit_type="tank", label="Feed Tank", section_id="feed_handling"),
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["feed_handling", "reaction"],
            stream_ids=["S1", "S2"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Feed",
                    temperature_c=25.0,
                    pressure_bar=1.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="TK-101",
                    stream_role="feed",
                    section_id="feed_handling",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="Transfer",
                    temperature_c=40.0,
                    pressure_bar=2.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="TK-101",
                    destination_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_3",
            route_id="route_3",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamSpec(stream_id="S2", source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)

        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )

        self.assertIn("Feed_Handling", artifact.sheets[0].svg)
        self.assertIn("Reaction", artifact.sheets[1].svg)
        self.assertIn("sheet_2", artifact.sheets[0].svg)

    def test_pfd_svg_regression_signature_matches_fixture(self):
        artifact, *_ = self._build_phase4_regression_artifact()
        expected = self._fixture_path("pfd_phase4_signature.txt").read_text()
        actual = self._pfd_svg_regression_signature(artifact)
        self.assertEqual(actual, expected)

    def test_phase4_module_layout_keeps_nodes_inside_module_and_non_overlapping(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_layout",
            route_id="route_layout",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="E-101", unit_type="heat_exchanger", label="Feed/Effluent Exchanger", section_id="reaction"),
                FlowsheetNode(node_id="P-101", unit_type="pump", label="Recycle Pump", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S1", "S2", "S3"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Feed to reactor",
                    temperature_c=25.0,
                    pressure_bar=1.0,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="R-101",
                    stream_role="feed",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="Hot effluent to exchanger",
                    temperature_c=90.0,
                    pressure_bar=3.0,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=9.0, molar_flow_kmol_hr=0.09)],
                    source_unit_id="R-101",
                    destination_unit_id="E-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S3",
                    description="Recycle through pump",
                    temperature_c=50.0,
                    pressure_bar=2.5,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=4.0, molar_flow_kmol_hr=0.04)],
                    source_unit_id="E-101",
                    destination_unit_id="P-101",
                    stream_role="recycle",
                    section_id="reaction",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_layout",
            route_id="route_layout",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="R-101", stream_role="feed", section_id="reaction"),
                StreamSpec(stream_id="S2", source_unit_id="R-101", destination_unit_id="E-101", stream_role="intermediate", section_id="reaction"),
                StreamSpec(stream_id="S3", source_unit_id="E-101", destination_unit_id="P-101", stream_role="recycle", section_id="reaction"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )

        sheet = artifact.sheets[0]
        reaction_module = next(module for module in modules.modules if module.section_id == "reaction")
        placement = next(item for item in composition.sheets[0].module_placements if item.module_id == reaction_module.module_id)
        module_nodes = [node for node in artifact.nodes if node.node_id in reaction_module.entity_ids]

        for node in module_nodes:
            self.assertGreaterEqual(node.x, placement.x)
            self.assertGreaterEqual(node.y, placement.y)
            self.assertLessEqual(node.x + node.width, placement.x + placement.width + 1)
            self.assertLessEqual(node.y + node.height, placement.y + placement.height + 1)

        for left_index, left in enumerate(module_nodes):
            for right in module_nodes[left_index + 1 :]:
                overlaps_x = left.x < right.x + right.width and right.x < left.x + left.width
                overlaps_y = left.y < right.y + right.height and right.y < left.y + left.height
                self.assertFalse(overlaps_x and overlaps_y)

    def test_phase4_edge_label_resolution_avoids_node_collisions(self):
        sheet = DiagramSheet(sheet_id="sheet_1", title="PFD Sheet 1", width_px=900, height_px=420)
        nodes = [
            DiagramNode(node_id="SRC", label="Source", node_family="tank", x=80, y=140, width=140, height=80),
            DiagramNode(node_id="MID", label="Blocking Vessel", node_family="vessel", x=250, y=84, width=160, height=112),
            DiagramNode(node_id="DST", label="Target", node_family="vessel", x=560, y=140, width=140, height=80),
        ]

        default_rect = _label_bounds(330.0, 120.0, "S-201: reactor effluent", 28, 11)
        blocking_rect = (nodes[1].x, nodes[1].y, nodes[1].width, nodes[1].height)
        self.assertTrue(_rectangles_overlap(default_rect, blocking_rect, padding=8.0))

        resolved_x, resolved_y = _resolve_edge_label_position(330.0, 120.0, "S-201: reactor effluent", 28, 11, nodes, sheet=sheet)
        resolved_rect = _label_bounds(resolved_x, resolved_y, "S-201: reactor effluent", 28, 11)

        self.assertFalse(_rectangles_overlap(resolved_rect, blocking_rect, padding=8.0))

    def test_phase4_edge_label_resolution_avoids_node_label_boxes(self):
        sheet = DiagramSheet(sheet_id="sheet_1", title="Utility Overview", width_px=900, height_px=420)
        nodes = [
            DiagramNode(
                node_id="N-1",
                label="Reactor",
                node_family="reactor",
                x=210,
                y=110,
                width=190,
                height=150,
                labels=[DiagramLabel(text="R-101", kind="primary"), DiagramLabel(text="Main Reactor", kind="secondary")],
            ),
        ]
        obstacles = _node_label_bounds_for_rendering(nodes, sheet.title)
        default_rect = _label_bounds(305.0, 134.0, "S-101: feed stream", 28, 11)
        self.assertTrue(any(_rectangles_overlap(default_rect, obstacle, padding=6.0) for obstacle in obstacles))

        resolved_x, resolved_y = _resolve_edge_label_position(
            305.0,
            134.0,
            "S-101: feed stream",
            28,
            11,
            nodes,
            sheet=sheet,
            route_points=[(80.0, 134.0), (520.0, 134.0)],
            obstacle_rects=obstacles,
        )
        resolved_rect = _label_bounds(resolved_x, resolved_y, "S-101: feed stream", 28, 11)

        self.assertFalse(any(_rectangles_overlap(resolved_rect, obstacle, padding=6.0) for obstacle in obstacles))
        self.assertFalse(_path_intersects_rect([(80.0, 134.0), (520.0, 134.0)], resolved_rect, padding=4.0))

    def test_phase4_generic_node_labels_are_vertically_distributed(self):
        node = DiagramNode(
            node_id="R-101",
            label="Reactor",
            node_family="reactor",
            x=120,
            y=90,
            width=190,
            height=150,
            labels=[
                DiagramLabel(text="R-101", kind="primary"),
                DiagramLabel(text="Main Reactor Service", kind="secondary"),
                DiagramLabel(text="+120 kW heat duty", kind="utility"),
            ],
        )

        styles = _node_label_render_styles(node, "Utility Overview")

        self.assertEqual(len(styles), 3)
        self.assertLess(float(styles[0]["y"]), float(styles[1]["y"]))
        self.assertLess(float(styles[1]["y"]), float(styles[2]["y"]))
        self.assertGreater(float(styles[2]["y"]), node.y + node.height * 0.7)

        bounds = _node_label_bounds_for_rendering([node], "Utility Overview")
        for left_index, left in enumerate(bounds):
            for right in bounds[left_index + 1 :]:
                self.assertFalse(_rectangles_overlap(left, right, padding=2.0))

    def test_phase4_column_label_policy_uses_top_biased_spacing(self):
        node = DiagramNode(
            node_id="C-101",
            label="Column",
            node_family="column",
            x=160,
            y=80,
            width=150,
            height=190,
            labels=[
                DiagramLabel(text="C-101", kind="primary"),
                DiagramLabel(text="Distillation Column", kind="secondary"),
                DiagramLabel(text="Overhead reflux", kind="utility"),
            ],
        )

        styles = _node_label_render_styles(node, "Utility Overview")

        self.assertLess(float(styles[0]["y"]), node.y + node.height * 0.35)
        self.assertLess(float(styles[1]["y"]), float(styles[2]["y"]))
        self.assertGreater(float(styles[2]["y"]), node.y + node.height * 0.7)
        self.assertEqual(int(styles[0]["wrap"]), 12)

    def test_phase4_compact_pump_label_policy_stays_non_overlapping(self):
        node = DiagramNode(
            node_id="P-101",
            label="Pump",
            node_family="pump",
            x=120,
            y=110,
            width=170,
            height=92,
            labels=[
                DiagramLabel(text="P-101", kind="primary"),
                DiagramLabel(text="Recycle Pump", kind="secondary"),
                DiagramLabel(text="+15 kW motor", kind="utility"),
            ],
        )

        styles = _node_label_render_styles(node, "Utility Overview")
        bounds = _node_label_bounds_for_rendering([node], "Utility Overview")

        self.assertEqual(len(styles), 3)
        self.assertLess(float(styles[0]["y"]), float(styles[1]["y"]))
        self.assertLess(float(styles[1]["y"]), float(styles[2]["y"]))
        self.assertEqual(int(styles[2]["font_size"]), 9)
        for left_index, left in enumerate(bounds):
            for right in bounds[left_index + 1 :]:
                self.assertFalse(_rectangles_overlap(left, right, padding=2.0))

    def test_phase4_module_layout_uses_label_aware_node_footprints(self):
        left = DiagramNode(
            node_id="E-101",
            label="Exchanger",
            node_family="heat exchanger",
            x=0.0,
            y=0.0,
            width=205,
            height=104,
            labels=[
                DiagramLabel(text="E-101", kind="primary"),
                DiagramLabel(text="Very Long Feed Effluent Heat Exchanger Service", kind="secondary"),
            ],
        )
        right = DiagramNode(
            node_id="E-102",
            label="Exchanger",
            node_family="heat exchanger",
            x=0.0,
            y=0.0,
            width=205,
            height=104,
            labels=[
                DiagramLabel(text="E-102", kind="primary"),
                DiagramLabel(text="Very Long Product Cooler Service Description", kind="secondary"),
            ],
        )
        short_left = DiagramNode(
            node_id="E-201",
            label="Exchanger",
            node_family="heat exchanger",
            x=0.0,
            y=0.0,
            width=205,
            height=104,
            labels=[DiagramLabel(text="E-201", kind="primary"), DiagramLabel(text="Cooler", kind="secondary")],
        )
        short_right = DiagramNode(
            node_id="E-202",
            label="Exchanger",
            node_family="heat exchanger",
            x=0.0,
            y=0.0,
            width=205,
            height=104,
            labels=[DiagramLabel(text="E-202", kind="primary"), DiagramLabel(text="Heater", kind="secondary")],
        )
        placement = DiagramModulePlacement(module_id="m1", sheet_id="sheet_1", x=80, y=80, width=760, height=240)
        module = DiagramModuleSpec(
            module_id="m1",
            module_kind=DiagramLevel.PFD,
            title="Exchange",
            symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
            section_id="reaction",
        )

        _layout_module_nodes([left, right], placement, module=module)
        _layout_module_nodes([short_left, short_right], placement, module=module)
        bounds = _node_label_bounds_for_rendering([left, right], "Utility Overview")

        self.assertGreater(right.x - left.x, short_right.x - short_left.x)
        self.assertGreaterEqual(_node_layout_footprint(left)[0], left.width)
        self.assertGreaterEqual(_node_layout_footprint(right)[0], right.width)
        for left_index, left_bound in enumerate(bounds):
            for right_bound in bounds[left_index + 1 :]:
                self.assertFalse(_rectangles_overlap(left_bound, right_bound, padding=2.0))

    def test_phase4_intra_module_route_hints_use_local_orthogonal_paths(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_route_local",
            route_id="route_local",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="E-101", unit_type="heat_exchanger", label="Feed/Effluent Exchanger", section_id="reaction"),
                FlowsheetNode(node_id="P-101", unit_type="pump", label="Recycle Pump", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S1", "S2"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Hot effluent to exchanger",
                    temperature_c=90.0,
                    pressure_bar=3.0,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=9.0, molar_flow_kmol_hr=0.09)],
                    source_unit_id="R-101",
                    destination_unit_id="E-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="Recycle through pump",
                    temperature_c=50.0,
                    pressure_bar=2.5,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=4.0, molar_flow_kmol_hr=0.04)],
                    source_unit_id="E-101",
                    destination_unit_id="P-101",
                    stream_role="recycle",
                    section_id="reaction",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_route_local",
            route_id="route_local",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", source_unit_id="R-101", destination_unit_id="E-101", stream_role="intermediate", section_id="reaction"),
                StreamSpec(stream_id="S2", source_unit_id="E-101", destination_unit_id="P-101", stream_role="recycle", section_id="reaction"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )

        sheet = artifact.sheets[0]
        sheet_nodes = [node for node in artifact.nodes if node.node_id in sheet.node_ids]
        sheet_edges = [edge for edge in artifact.edges if edge.sheet_id == sheet.sheet_id]
        route_hints = _build_pfd_sheet_route_hints(sheet.sheet_id, sheet_edges, sheet_nodes, modules, composition)

        reaction_edge = next(edge for edge in sheet_edges if edge.source_node_id == "R-101" and edge.target_node_id == "E-101")
        recycle_edge = next(edge for edge in sheet_edges if edge.source_node_id == "E-101" and edge.target_node_id == "P-101")
        reaction_hint = route_hints[reaction_edge.edge_id]
        recycle_hint = route_hints[recycle_edge.edge_id]

        self.assertGreaterEqual(len(reaction_hint["points"]), 3)
        for left, right in zip(reaction_hint["points"], reaction_hint["points"][1:]):
            self.assertTrue(abs(left[0] - right[0]) < 0.1 or abs(left[1] - right[1]) < 0.1)
        self.assertAlmostEqual(reaction_hint["points"][0][0], reaction_hint["points"][1][0], delta=0.1)
        self.assertAlmostEqual(reaction_hint["points"][1][0], reaction_hint["points"][-1][0], delta=0.1)
        self.assertLess(reaction_hint["points"][0][1], reaction_hint["points"][-1][1])

        self.assertGreaterEqual(len(recycle_hint["points"]), 3)
        for left, right in zip(recycle_hint["points"], recycle_hint["points"][1:]):
            self.assertTrue(abs(left[0] - right[0]) < 0.1 or abs(left[1] - right[1]) < 0.1)
        self.assertLess(recycle_hint["points"][1][1], recycle_hint["points"][0][1])
        self.assertNotAlmostEqual(recycle_hint["points"][1][1], recycle_hint["points"][-1][1], delta=0.1)

        routing = build_process_flow_diagram_routing_artifact(semantics, modules, composition, artifact)
        self.assertEqual(len(routing.sheets), len(artifact.sheets))
        self.assertGreaterEqual(len(routing.sheets[0].route_hints), 2)
        self.assertTrue(any(hint.edge_id == reaction_edge.edge_id for hint in routing.sheets[0].route_hints))
        self.assertGreaterEqual(routing.sheets[0].max_channel_load, 1)

    def test_phase14_routing_artifact_reports_crossings_and_congestion(self):
        route_hints = {
            "e1": {"points": [(100.0, 100.0), (100.0, 200.0), (240.0, 200.0)]},
            "e2": {"points": [(60.0, 160.0), (180.0, 160.0), (180.0, 260.0)]},
            "e3": {"points": [(100.0, 120.0), (100.0, 220.0)]},
            "e4": {"points": [(100.0, 140.0), (100.0, 240.0)]},
            "e5": {"points": [(100.0, 150.0), (100.0, 250.0)]},
        }

        crossings, congested, max_load = _routing_quality_metrics(route_hints)

        self.assertGreaterEqual(crossings, 1)
        self.assertGreaterEqual(congested, 1)
        self.assertGreaterEqual(max_load, 4)

    def test_phase14_route_optimizer_reduces_shared_channel_load(self):
        route_hints = {
            "e1": {"points": [(40.0, 80.0), (40.0, 120.0), (150.0, 120.0), (150.0, 240.0), (260.0, 240.0), (260.0, 300.0)]},
            "e2": {"points": [(55.0, 90.0), (55.0, 140.0), (150.0, 140.0), (150.0, 250.0), (275.0, 250.0), (275.0, 315.0)]},
            "e3": {"points": [(70.0, 100.0), (70.0, 160.0), (150.0, 160.0), (150.0, 260.0), (290.0, 260.0), (290.0, 330.0)]},
            "e4": {"points": [(85.0, 110.0), (85.0, 180.0), (150.0, 180.0), (150.0, 270.0), (305.0, 270.0), (305.0, 345.0)]},
        }

        original_metrics = _routing_quality_metrics(route_hints)
        optimized = _optimize_pfd_route_hints(route_hints, 420, 420)
        optimized_metrics = _routing_quality_metrics(optimized)

        self.assertGreaterEqual(original_metrics[1], 1)
        self.assertLess(optimized_metrics[0], original_metrics[0])
        self.assertLessEqual(optimized_metrics[1], original_metrics[1])

    def test_phase14_connector_lane_reservations_fan_out_parallel_connectors(self):
        modules = DiagramModuleArtifact(
            diagram_id="connector_modules",
            route_id="route_connector",
            module_kind=DiagramLevel.PFD,
            modules=[
                DiagramModuleSpec(
                    module_id="m_left",
                    module_kind=DiagramLevel.PFD,
                    title="Left",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    entity_ids=["A"],
                    boundary_ports=[
                        DiagramModulePort(port_id="m_left__c1__out", entity_id="A", side=DiagramPortSide.RIGHT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_left__c2__out", entity_id="A", side=DiagramPortSide.RIGHT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_left__c3__out", entity_id="A", side=DiagramPortSide.RIGHT, connection_role=DiagramEdgeRole.PROCESS),
                    ],
                ),
                DiagramModuleSpec(
                    module_id="m_right",
                    module_kind=DiagramLevel.PFD,
                    title="Right",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    entity_ids=["B"],
                    boundary_ports=[
                        DiagramModulePort(port_id="m_right__c1__in", entity_id="B", side=DiagramPortSide.LEFT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_right__c2__in", entity_id="B", side=DiagramPortSide.LEFT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_right__c3__in", entity_id="B", side=DiagramPortSide.LEFT, connection_role=DiagramEdgeRole.PROCESS),
                    ],
                ),
            ],
            markdown="seed",
        )
        composition = DiagramSheetCompositionArtifact(
            diagram_id="connector_comp",
            route_id="route_connector",
            diagram_level=DiagramLevel.PFD,
            sheets=[
                DiagramSheetComposition(
                    sheet_id="sheet_1",
                    title="Process Flow Diagram",
                    diagram_level=DiagramLevel.PFD,
                    width_px=1200,
                    height_px=700,
                    module_placements=[
                        DiagramModulePlacement(module_id="m_left", sheet_id="sheet_1", x=120, y=180, width=260, height=220),
                        DiagramModulePlacement(module_id="m_right", sheet_id="sheet_1", x=700, y=180, width=260, height=220),
                    ],
                    connectors=[
                        DiagramInterModuleConnector(connector_id="sheet_connector_c1", role=DiagramEdgeRole.PROCESS, source_module_id="m_left", source_port_id="m_left__c1__out", target_module_id="m_right", target_port_id="m_right__c1__in"),
                        DiagramInterModuleConnector(connector_id="sheet_connector_c2", role=DiagramEdgeRole.PROCESS, source_module_id="m_left", source_port_id="m_left__c2__out", target_module_id="m_right", target_port_id="m_right__c2__in"),
                        DiagramInterModuleConnector(connector_id="sheet_connector_c3", role=DiagramEdgeRole.PROCESS, source_module_id="m_left", source_port_id="m_left__c3__out", target_module_id="m_right", target_port_id="m_right__c3__in"),
                    ],
                )
            ],
            markdown="seed",
        )
        nodes = [
            DiagramNode(node_id="A", label="A", node_family="tank", x=180, y=220, width=180, height=120),
            DiagramNode(node_id="B", label="B", node_family="reactor", x=760, y=220, width=180, height=120),
        ]
        edges = [
            DiagramEdge(edge_id="e1", source_node_id="A", target_node_id="B", edge_type="main", sheet_id="sheet_1", notes="connection=c1"),
            DiagramEdge(edge_id="e2", source_node_id="A", target_node_id="B", edge_type="main", sheet_id="sheet_1", notes="connection=c2"),
            DiagramEdge(edge_id="e3", source_node_id="A", target_node_id="B", edge_type="main", sheet_id="sheet_1", notes="connection=c3"),
        ]

        reservations = _build_pfd_connector_lane_reservations(composition.sheets[0], modules)
        route_hints = _build_pfd_sheet_route_hints("sheet_1", edges, nodes, modules, composition)
        reserved_mid_x = {round(values["mid_x"], 1) for values in reservations.values() if "mid_x" in values}
        hint_mid_x = {round(route_hints[edge.edge_id]["points"][2][0], 1) for edge in edges}

        self.assertEqual(len(reserved_mid_x), 3)
        self.assertGreaterEqual(len(hint_mid_x), 2)

    def test_phase15_equipment_template_library_covers_core_families(self):
        templates = build_diagram_equipment_templates()
        family_map = {template.family: template for template in templates.templates}

        self.assertIn("reactor", family_map)
        self.assertIn("column", family_map)
        self.assertIn("heat_exchanger", family_map)
        self.assertIn("vessel", family_map)
        self.assertEqual(family_map["reactor"].pfd_symbol_key, "pfd_reactor")
        self.assertTrue(any(port.port_role == "safeguard" and port.side == DiagramPortSide.TOP for port in family_map["reactor"].ports))
        self.assertTrue(any(port.port_role == "bottoms" and port.side == DiagramPortSide.BOTTOM for port in family_map["column"].ports))

    def test_phase16_domain_pack_library_and_target_selection(self):
        packs = build_diagram_domain_packs()
        pack_map = {pack.pack_id: pack for pack in packs.packs}

        self.assertIn("specialty_chemicals", pack_map)
        self.assertIn("petrochemicals", pack_map)
        self.assertIn("utility_dense_process", pack_map)
        self.assertIn("fuel_gas", pack_map["petrochemicals"].major_stream_roles)
        self.assertIn("utilities", pack_map["utility_dense_process"].required_bfd_sections)

        petro_target = build_diagram_target_profile(ProjectBasis(target_product="Ethylene Oxide", capacity_tpa=1000, target_purity_wt_pct=99.0))
        utility_target = build_diagram_target_profile(ProjectBasis(target_product="Utility Steam Recovery System", capacity_tpa=1000, target_purity_wt_pct=99.0))
        specialty_target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))

        self.assertEqual(petro_target.domain_pack_id, "petrochemicals")
        self.assertIn("fuel_gas", petro_target.major_stream_roles)
        self.assertEqual(petro_target.connector_mid_x_spacing_px, 24)
        self.assertEqual(utility_target.domain_pack_id, "utility_dense_process")
        self.assertIn("utilities", utility_target.required_bfd_sections)
        self.assertEqual(utility_target.main_body_max_pfd_nodes, 5)
        self.assertEqual(utility_target.connector_lane_y_spacing_px, 22)
        self.assertEqual(specialty_target.domain_pack_id, "specialty_chemicals")

    def test_phase16_domain_equipment_template_overrides_apply(self):
        base = build_diagram_equipment_templates()
        petro = build_domain_equipment_templates("petrochemicals")
        utility = build_domain_equipment_templates("utility_dense_process")

        base_column = next(template for template in base.templates if template.family == "column")
        petro_column = next(template for template in petro.templates if template.family == "column")
        base_exchanger = next(template for template in base.templates if template.family == "heat_exchanger")
        utility_exchanger = next(template for template in utility.templates if template.family == "heat_exchanger")

        self.assertEqual(petro.artifact_id, "diagram_equipment_templates_v1_petrochemicals")
        self.assertGreater(petro_column.default_height_px, base_column.default_height_px)
        self.assertEqual(petro_column.template_id, "template_column_petrochemical")
        self.assertGreater(utility_exchanger.default_width_px, base_exchanger.default_width_px)
        self.assertEqual(utility_exchanger.template_id, "template_heat_exchanger_utility_dense")

    def test_phase16_domain_pack_influences_ambiguous_template_selection(self):
        library = build_diagram_symbol_library()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_phase16_domain",
            route_id="route_phase16_domain",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="U-101", unit_type="separator column", label="Separator Column", section_id="separation")],
            unit_models=[],
            section_ids=["separation"],
            stream_ids=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_phase16_domain",
            route_id="route_phase16_domain",
            operating_mode="continuous",
            units=[],
            streams=[],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(streams=[], closure_error_pct=0.0, markdown="seed", citations=["s1"], assumptions=["seed"])

        petro_target = build_diagram_target_profile(ProjectBasis(target_product="Ethylene Oxide", capacity_tpa=1000, target_purity_wt_pct=99.0))
        specialty_target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))

        petro = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, petro_target, library)
        specialty = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, specialty_target, library)

        self.assertEqual(petro.entities[0].metadata.get("template_id"), "template_column_petrochemical")
        self.assertEqual(petro.entities[0].metadata.get("template_family"), "column")
        self.assertEqual(specialty.entities[0].metadata.get("template_family"), "vessel")

    def test_phase16_domain_pack_symbol_policy_limits_disallowed_units(self):
        library = build_diagram_symbol_library()
        target = build_diagram_target_profile(ProjectBasis(target_product="Utility Steam Recovery System", capacity_tpa=1000, target_purity_wt_pct=99.0))
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_phase16_symbol_policy",
            route_id="route_phase16_symbol_policy",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="C-101", unit_type="distillation column", label="Column", section_id="purification")],
            unit_models=[],
            section_ids=["purification"],
            stream_ids=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_phase16_symbol_policy",
            route_id="route_phase16_symbol_policy",
            operating_mode="continuous",
            units=[],
            streams=[],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(streams=[], closure_error_pct=0.0, markdown="seed", citations=["s1"], assumptions=["seed"])

        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)

        self.assertEqual(target.domain_pack_id, "utility_dense_process")
        self.assertNotIn("pfd_column", target.allowed_pfd_symbol_keys)
        self.assertEqual(semantics.entities[0].symbol_key, "pfd_vessel")

    def test_phase16_domain_pack_changes_connector_lane_spacing(self):
        modules = DiagramModuleArtifact(
            diagram_id="connector_modules",
            route_id="route_connector",
            module_kind=DiagramLevel.PFD,
            modules=[
                DiagramModuleSpec(
                    module_id="m_left",
                    module_kind=DiagramLevel.PFD,
                    title="Left",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    boundary_ports=[
                        DiagramModulePort(port_id="m_left__c1__out", entity_id="A", side=DiagramPortSide.RIGHT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_left__c2__out", entity_id="A", side=DiagramPortSide.RIGHT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_left__c3__out", entity_id="A", side=DiagramPortSide.RIGHT, connection_role=DiagramEdgeRole.PROCESS),
                    ],
                ),
                DiagramModuleSpec(
                    module_id="m_right",
                    module_kind=DiagramLevel.PFD,
                    title="Right",
                    symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
                    boundary_ports=[
                        DiagramModulePort(port_id="m_right__c1__in", entity_id="B", side=DiagramPortSide.LEFT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_right__c2__in", entity_id="B", side=DiagramPortSide.LEFT, connection_role=DiagramEdgeRole.PROCESS),
                        DiagramModulePort(port_id="m_right__c3__in", entity_id="B", side=DiagramPortSide.LEFT, connection_role=DiagramEdgeRole.PROCESS),
                    ],
                ),
            ],
        )
        composition = DiagramSheetComposition(
            sheet_id="sheet_1",
            title="Connectors",
            diagram_level=DiagramLevel.PFD,
            module_placements=[
                DiagramModulePlacement(module_id="m_left", sheet_id="sheet_1", x=120.0, y=140.0, width=220.0, height=180.0),
                DiagramModulePlacement(module_id="m_right", sheet_id="sheet_1", x=560.0, y=140.0, width=220.0, height=180.0),
            ],
            connectors=[
                DiagramInterModuleConnector(connector_id="sheet_connector_c1", role=DiagramEdgeRole.PROCESS, source_module_id="m_left", source_port_id="m_left__c1__out", target_module_id="m_right", target_port_id="m_right__c1__in"),
                DiagramInterModuleConnector(connector_id="sheet_connector_c2", role=DiagramEdgeRole.PROCESS, source_module_id="m_left", source_port_id="m_left__c2__out", target_module_id="m_right", target_port_id="m_right__c2__in"),
                DiagramInterModuleConnector(connector_id="sheet_connector_c3", role=DiagramEdgeRole.PROCESS, source_module_id="m_left", source_port_id="m_left__c3__out", target_module_id="m_right", target_port_id="m_right__c3__in"),
            ],
        )
        petro_target = build_diagram_target_profile(ProjectBasis(target_product="Ethylene Oxide", capacity_tpa=1000, target_purity_wt_pct=99.0))
        utility_target = build_diagram_target_profile(ProjectBasis(target_product="Utility Steam Recovery System", capacity_tpa=1000, target_purity_wt_pct=99.0))

        petro = _build_pfd_connector_lane_reservations(composition, modules, petro_target)
        utility = _build_pfd_connector_lane_reservations(composition, modules, utility_target)

        petro_mid_x = sorted(round(item["mid_x"], 1) for item in petro.values())
        utility_mid_x = sorted(round(item["mid_x"], 1) for item in utility.values())

        self.assertGreater(utility_mid_x[-1] - utility_mid_x[0], petro_mid_x[-1] - petro_mid_x[0])

    def test_phase16_domain_pack_changes_sheet_width_budget(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_phase16_sheet_budget",
            route_id="route_phase16_sheet_budget",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="E-101", unit_type="heat_exchanger", label="Long Exchanger A", section_id="s1"),
                FlowsheetNode(node_id="P-101", unit_type="pump", label="Pump A", section_id="s1"),
                FlowsheetNode(node_id="E-201", unit_type="heat_exchanger", label="Long Exchanger B", section_id="s2"),
                FlowsheetNode(node_id="P-201", unit_type="pump", label="Pump B", section_id="s2"),
                FlowsheetNode(node_id="E-301", unit_type="heat_exchanger", label="Long Exchanger C", section_id="s3"),
                FlowsheetNode(node_id="P-301", unit_type="pump", label="Pump C", section_id="s3"),
            ],
            unit_models=[],
            section_ids=["s1", "s2", "s3"],
            stream_ids=["S1", "S2"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_phase16_sheet_budget",
            route_id="route_phase16_sheet_budget",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", source_unit_id="P-101", destination_unit_id="E-201", stream_role="intermediate", section_id="s2"),
                StreamSpec(stream_id="S2", source_unit_id="P-201", destination_unit_id="E-301", stream_role="intermediate", section_id="s3"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(stream_id="S1", description="transfer", temperature_c=35.0, pressure_bar=2.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=1.0, molar_flow_kmol_hr=0.01)], source_unit_id="P-101", destination_unit_id="E-201", stream_role="intermediate", section_id="s2"),
                StreamRecord(stream_id="S2", description="transfer", temperature_c=35.0, pressure_bar=2.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=1.0, molar_flow_kmol_hr=0.01)], source_unit_id="P-201", destination_unit_id="E-301", stream_role="intermediate", section_id="s3"),
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        petro_target = build_diagram_target_profile(ProjectBasis(target_product="Ethylene Oxide", capacity_tpa=1000, target_purity_wt_pct=99.0))
        utility_target = build_diagram_target_profile(ProjectBasis(target_product="Utility Steam Recovery System", capacity_tpa=1000, target_purity_wt_pct=99.0))

        petro_semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, petro_target, library)
        utility_semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, utility_target, library)
        petro_modules = build_process_flow_diagram_modules(petro_semantics, library)
        utility_modules = build_process_flow_diagram_modules(utility_semantics, library)
        petro_comp = build_process_flow_diagram_sheet_composition(petro_modules, petro_semantics, style, petro_target)
        utility_comp = build_process_flow_diagram_sheet_composition(utility_modules, utility_semantics, style, utility_target)

        petro_span = max((p.x + p.width for p in petro_comp.sheets[0].module_placements), default=0.0) - min((p.x for p in petro_comp.sheets[0].module_placements), default=0.0)
        utility_span = max((p.x + p.width for p in utility_comp.sheets[0].module_placements), default=0.0) - min((p.x for p in utility_comp.sheets[0].module_placements), default=0.0)

        self.assertLessEqual(utility_span, petro_span)

    def test_phase15_template_defaults_drive_common_node_dimensions(self):
        reactor = DiagramNode(node_id="R", label="Reactor", node_family="reactor")
        column = DiagramNode(node_id="C", label="Column", node_family="column")
        exchanger = DiagramNode(node_id="E", label="Exchanger", node_family="heat exchanger")
        terminal = DiagramNode(node_id="T", label="Terminal", node_family="terminal")

        _apply_pfd_node_dimensions(reactor)
        _apply_pfd_node_dimensions(column)
        _apply_pfd_node_dimensions(exchanger)
        _apply_pfd_node_dimensions(terminal)

        self.assertEqual((reactor.width, reactor.height), (190, 150))
        self.assertEqual((column.width, column.height), (150, 190))
        self.assertEqual((exchanger.width, exchanger.height), (205, 104))
        self.assertEqual((terminal.width, terminal.height), (120, 80))

    def test_phase15_template_port_maps_drive_connection_points(self):
        column = DiagramNode(
            node_id="C-101",
            label="Column",
            node_family="column",
            x=120.0,
            y=80.0,
            width=150.0,
            height=190.0,
            notes="template_family=column",
        )
        overhead = _node_connection_point(column, "top", "overhead")
        bottoms = _node_connection_point(column, "bottom", "bottoms")
        inlet = _node_connection_point(column, "left", "process_inlet")
        outlet = _node_connection_point(column, "right", "process_outlet")

        self.assertAlmostEqual(overhead[0], column.x + column.width / 2, places=1)
        self.assertAlmostEqual(overhead[1], column.y + column.height * 0.02, places=1)
        self.assertAlmostEqual(bottoms[0], column.x + column.width / 2, places=1)
        self.assertAlmostEqual(bottoms[1], column.y + column.height * 0.98, places=1)
        self.assertLess(inlet[1], column.y + column.height / 2)
        self.assertLess(outlet[1], column.y + column.height / 2)

        exchanger = DiagramNode(
            node_id="E-101",
            label="Exchanger",
            node_family="heat exchanger",
            x=300.0,
            y=120.0,
            width=205.0,
            height=104.0,
            notes="template_family=heat_exchanger",
        )
        utility_in = _node_connection_point(exchanger, "top", "utility_inlet")
        utility_out = _node_connection_point(exchanger, "bottom", "utility_outlet")

        self.assertGreater(utility_in[0], exchanger.x + exchanger.width / 2)
        self.assertAlmostEqual(utility_in[1], exchanger.y, places=1)
        self.assertLess(utility_out[0], exchanger.x + exchanger.width / 2)
        self.assertAlmostEqual(utility_out[1], exchanger.y + exchanger.height, places=1)

    def test_phase15_pfd_semantics_and_modules_use_template_metadata_and_port_sides(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_phase15_templates",
            route_id="route_phase15_templates",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="V-101", unit_type="flash_vessel", label="Flash Drum", section_id="recovery")],
            unit_models=[],
            section_ids=["recovery"],
            stream_ids=["S1", "S2", "S3"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Feed to drum",
                    temperature_c=40.0,
                    pressure_bar=1.4,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    destination_unit_id="V-101",
                    stream_role="feed",
                    section_id="recovery",
                ),
                StreamRecord(
                    stream_id="S2",
                    description="Vent",
                    temperature_c=60.0,
                    pressure_bar=1.2,
                    components=[StreamComponentFlow(name="A", mass_flow_kg_hr=1.0, molar_flow_kmol_hr=0.01)],
                    source_unit_id="V-101",
                    stream_role="vent",
                    section_id="recovery",
                ),
                StreamRecord(
                    stream_id="S3",
                    description="Bottoms",
                    temperature_c=78.0,
                    pressure_bar=1.5,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.08)],
                    source_unit_id="V-101",
                    stream_role="waste",
                    section_id="recovery",
                ),
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_phase15_templates",
            route_id="route_phase15_templates",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="V-101", stream_role="feed", section_id="recovery"),
                StreamSpec(stream_id="S2", source_unit_id="V-101", stream_role="vent", section_id="recovery"),
                StreamSpec(stream_id="S3", source_unit_id="V-101", stream_role="waste", section_id="recovery"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        vessel_entity = next(entity for entity in semantics.entities if entity.entity_id == "V-101")
        vessel_module = modules.modules[0]
        vent_port = next(port for port in vessel_module.boundary_ports if port.connection_role == DiagramEdgeRole.VENT)
        waste_port = next(port for port in vessel_module.boundary_ports if port.connection_role == DiagramEdgeRole.WASTE)

        self.assertEqual(vessel_entity.metadata.get("template_family"), "vessel")
        self.assertTrue(vessel_entity.metadata.get("template_id", "").startswith("template_"))
        self.assertEqual(vent_port.template_port_role, "vent")
        self.assertEqual(waste_port.template_port_role, "drain")
        self.assertEqual(vent_port.side, DiagramPortSide.TOP)
        self.assertEqual(waste_port.side, DiagramPortSide.BOTTOM)

    def test_phase15_rendered_pfd_carries_template_port_metadata(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_phase15_rendered_ports",
            route_id="route_phase15_rendered_ports",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="D-101", unit_type="distillation column", label="Main Column", section_id="purification"),
                FlowsheetNode(node_id="TK-101", unit_type="storage tank", label="Product Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["purification", "storage"],
            stream_ids=["S1"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_phase15_rendered_ports",
            route_id="route_phase15_rendered_ports",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(
                    stream_id="S1",
                    source_unit_id="D-101",
                    destination_unit_id="TK-101",
                    stream_role="product",
                    section_id="purification",
                )
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Overhead product",
                    temperature_c=42.0,
                    pressure_bar=1.3,
                    components=[StreamComponentFlow(name="P", mass_flow_kg_hr=12.0, molar_flow_kmol_hr=0.2)],
                    source_unit_id="D-101",
                    destination_unit_id="TK-101",
                    stream_role="product",
                    section_id="purification",
                )
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            equipment=None,
            energy_balance=None,
            style=style,
            target=target,
            semantics=semantics,
            modules=modules,
            sheet_composition=composition,
        )

        column_node = next(node for node in artifact.nodes if node.node_id == "D-101")
        product_edge = next(edge for edge in artifact.edges if edge.stream_id == "S1")

        self.assertIn("template_id=template_column", column_node.notes)
        self.assertIn("template_family=column", column_node.notes)
        self.assertIn("source_port_role=overhead", product_edge.notes)
        self.assertIn("target_port_role=process_inlet", product_edge.notes)

    def test_phase15_drawio_export_uses_template_port_anchors(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_phase15_drawio_ports",
            route_id="route_phase15_drawio_ports",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="D-101", unit_type="distillation column", label="Main Column", section_id="purification"),
                FlowsheetNode(node_id="TK-101", unit_type="storage tank", label="Product Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["purification", "storage"],
            stream_ids=["S1"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_phase15_drawio_ports",
            route_id="route_phase15_drawio_ports",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(
                    stream_id="S1",
                    source_unit_id="D-101",
                    destination_unit_id="TK-101",
                    stream_role="product",
                    section_id="purification",
                )
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="Overhead product",
                    temperature_c=42.0,
                    pressure_bar=1.3,
                    components=[StreamComponentFlow(name="P", mass_flow_kg_hr=12.0, molar_flow_kmol_hr=0.2)],
                    source_unit_id="D-101",
                    destination_unit_id="TK-101",
                    stream_role="product",
                    section_id="purification",
                )
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            equipment=None,
            energy_balance=None,
            style=style,
            target=target,
            semantics=semantics,
            modules=modules,
            sheet_composition=composition,
        )
        routing = build_process_flow_diagram_routing_artifact(semantics, modules, composition, artifact)
        drawio = build_drawio_document(
            diagram_id="pfd_template_ports",
            title="PFD Template Ports",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            routing=routing,
        )

        self.assertIn("exitX=0.5;exitY=0.02", drawio)
        self.assertIn("entryX=0.0;entryY=0.45", drawio)

    def test_phase15_module_reserved_margins_expand_for_template_ports(self):
        generic = DiagramModuleSpec(
            module_id="generic",
            module_kind=DiagramLevel.PFD,
            title="Generic",
            symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
            boundary_ports=[
                DiagramModulePort(
                    port_id="generic_in",
                    entity_id="A",
                    connection_role=DiagramEdgeRole.PROCESS,
                    template_port_role="process_inlet",
                    side=DiagramPortSide.LEFT,
                ),
                DiagramModulePort(
                    port_id="generic_out",
                    entity_id="A",
                    connection_role=DiagramEdgeRole.PROCESS,
                    template_port_role="process_outlet",
                    side=DiagramPortSide.RIGHT,
                ),
            ],
        )
        rich = DiagramModuleSpec(
            module_id="rich",
            module_kind=DiagramLevel.PFD,
            title="Rich",
            symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
            boundary_ports=[
                DiagramModulePort(
                    port_id="ovhd",
                    entity_id="C",
                    connection_role=DiagramEdgeRole.PRODUCT,
                    template_port_role="overhead",
                    side=DiagramPortSide.TOP,
                ),
                DiagramModulePort(
                    port_id="safe",
                    entity_id="C",
                    connection_role=DiagramEdgeRole.SAFEGUARD,
                    template_port_role="safeguard",
                    side=DiagramPortSide.TOP,
                ),
                DiagramModulePort(
                    port_id="btm",
                    entity_id="C",
                    connection_role=DiagramEdgeRole.WASTE,
                    template_port_role="bottoms",
                    side=DiagramPortSide.BOTTOM,
                ),
                DiagramModulePort(
                    port_id="uti",
                    entity_id="C",
                    connection_role=DiagramEdgeRole.UTILITY,
                    template_port_role="utility_outlet",
                    side=DiagramPortSide.BOTTOM,
                ),
            ],
        )

        generic_margins = _module_reserved_margins(generic)
        rich_margins = _module_reserved_margins(rich)

        self.assertGreater(rich_margins["top"], generic_margins["top"])
        self.assertGreater(rich_margins["bottom"], generic_margins["bottom"])

    def test_phase15_svg_shape_adds_template_family_overlays(self):
        style = build_diagram_style_profile()
        column = DiagramNode(
            node_id="C-101",
            label="Column",
            node_family="column",
            x=120.0,
            y=80.0,
            width=150.0,
            height=190.0,
            notes="template_family=column",
        )
        exchanger = DiagramNode(
            node_id="E-101",
            label="Exchanger",
            node_family="heat exchanger",
            x=300.0,
            y=120.0,
            width=205.0,
            height=104.0,
            notes="template_family=heat_exchanger",
        )

        column_svg = "".join(_svg_node_shape(column, style))
        exchanger_svg = "".join(_svg_node_shape(exchanger, style))

        self.assertIn(f"cy='{column.y - 14:.1f}'", column_svg)
        self.assertIn(f"cy='{column.y + column.height + 14:.1f}'", column_svg)
        self.assertIn("#4a6fa5", exchanger_svg)
        self.assertIn(f"cy='{exchanger.y - 12:.1f}'", exchanger_svg)
        self.assertIn(f"cy='{exchanger.y + exchanger.height + 12:.1f}'", exchanger_svg)

    def test_phase4_intra_module_route_avoids_label_obstacle_when_possible(self):
        source = DiagramNode(node_id="SRC", label="Source", node_family="reactor", x=120, y=120, width=180, height=140)
        target = DiagramNode(node_id="DST", label="Target", node_family="vessel", x=420, y=120, width=180, height=140)
        placement = DiagramModulePlacement(module_id="m1", sheet_id="sheet_1", x=80, y=80, width=620, height=280)
        module = DiagramModuleSpec(
            module_id="m1",
            module_kind=DiagramLevel.PFD,
            title="Reaction",
            symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY,
            section_id="reaction",
        )
        edge = DiagramEdge(
            edge_id="e1",
            source_node_id="SRC",
            target_node_id="DST",
            edge_type="main",
            notes="lane=main",
        )
        obstacle = _label_bounds(360.0, 190.0, "Blocking label region", 24, 10)

        points = _pfd_route_points_within_module(source, target, placement, edge, module, obstacle_rects=[obstacle])

        self.assertFalse(_path_intersects_rect(points, obstacle, padding=4.0))
        for left, right in zip(points, points[1:]):
            self.assertTrue(abs(left[0] - right[0]) < 0.1 or abs(left[1] - right[1]) < 0.1)

    def test_phase4_sheet_composition_wraps_dense_wide_modules(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_dense_comp",
            route_id="route_dense_comp",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="E-101", unit_type="heat_exchanger", label="Very Long Feed Effluent Heat Exchanger Train A", section_id="s1"),
                FlowsheetNode(node_id="P-101", unit_type="pump", label="Recycle Pump A", section_id="s1"),
                FlowsheetNode(node_id="E-201", unit_type="heat_exchanger", label="Very Long Feed Effluent Heat Exchanger Train B", section_id="s2"),
                FlowsheetNode(node_id="P-201", unit_type="pump", label="Recycle Pump B", section_id="s2"),
                FlowsheetNode(node_id="E-301", unit_type="heat_exchanger", label="Very Long Feed Effluent Heat Exchanger Train C", section_id="s3"),
                FlowsheetNode(node_id="P-301", unit_type="pump", label="Recycle Pump C", section_id="s3"),
                FlowsheetNode(node_id="E-401", unit_type="heat_exchanger", label="Very Long Feed Effluent Heat Exchanger Train D", section_id="s4"),
                FlowsheetNode(node_id="P-401", unit_type="pump", label="Recycle Pump D", section_id="s4"),
            ],
            unit_models=[],
            section_ids=["s1", "s2", "s3", "s4"],
            stream_ids=["S1", "S2", "S3"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(stream_id="S1", description="transfer", temperature_c=40.0, pressure_bar=2.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=1.0, molar_flow_kmol_hr=0.01)], source_unit_id="P-101", destination_unit_id="E-201", stream_role="intermediate", section_id="s2"),
                StreamRecord(stream_id="S2", description="transfer", temperature_c=40.0, pressure_bar=2.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=1.0, molar_flow_kmol_hr=0.01)], source_unit_id="P-201", destination_unit_id="E-301", stream_role="intermediate", section_id="s3"),
                StreamRecord(stream_id="S3", description="transfer", temperature_c=40.0, pressure_bar=2.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=1.0, molar_flow_kmol_hr=0.01)], source_unit_id="P-301", destination_unit_id="E-401", stream_role="intermediate", section_id="s4"),
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_dense_comp",
            route_id="route_dense_comp",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", source_unit_id="P-101", destination_unit_id="E-201", stream_role="intermediate", section_id="s2"),
                StreamSpec(stream_id="S2", source_unit_id="P-201", destination_unit_id="E-301", stream_role="intermediate", section_id="s3"),
                StreamSpec(stream_id="S3", source_unit_id="P-301", destination_unit_id="E-401", stream_role="intermediate", section_id="s4"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)

        first_sheet = composition.sheets[0]
        distinct_rows = {round(placement.y, 1) for placement in first_sheet.module_placements}

        self.assertTrue(len(composition.sheets) > 1 or len(distinct_rows) > 1)
        self.assertGreaterEqual(first_sheet.height_px, style.canvas_height_px)

    def test_phase5_pfd_acceptance_marks_clean_case_complete(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_accept_clean",
            route_id="route_accept_clean",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="TK-101", unit_type="tank", label="Feed Tank", section_id="feed_handling"),
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["feed_handling", "reaction"],
            stream_ids=["S1", "S2"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(stream_id="S1", description="Feed", temperature_c=25.0, pressure_bar=1.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)], destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamRecord(stream_id="S2", description="To reactor", temperature_c=40.0, pressure_bar=2.0, components=[StreamComponentFlow(name="A", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)], source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
            ],
            closure_error_pct=0.1,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_accept_clean",
            route_id="route_accept_clean",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S1", destination_unit_id="TK-101", stream_role="feed", section_id="feed_handling"),
                StreamSpec(stream_id="S2", source_unit_id="TK-101", destination_unit_id="R-101", stream_role="intermediate", section_id="reaction"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            None,
            style,
            target,
            None,
            semantics,
            modules,
            composition,
        )
        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id=artifact.diagram_id,
            nodes=artifact.nodes,
            edges=artifact.edges,
            sheets=artifact.sheets,
            modules=modules,
            sheet_composition=composition,
            target=target,
            flowsheet_graph=flowsheet_graph,
            flowsheet_case=flowsheet_case,
        )

        self.assertEqual(acceptance.overall_status, "complete")
        self.assertEqual(acceptance.node_overlap_count, 0)
        self.assertEqual(acceptance.node_label_overlap_count, 0)
        self.assertEqual(acceptance.crowded_sheet_count, 0)
        self.assertGreaterEqual(acceptance.benchmark_cleanliness_score, 0.8)

    def test_phase5_pfd_acceptance_marks_crowded_case_conditional(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        sheets = [DiagramSheet(sheet_id="sheet_1", title="Process Flow Diagram", width_px=1200, height_px=700, node_ids=["A", "B", "C", "D"])]
        nodes = [
            DiagramNode(node_id="A", label="A", node_family="heat exchanger", x=80, y=180, width=260, height=140, labels=[DiagramLabel(text="E-101", kind="primary"), DiagramLabel(text="Very Long Exchanger Service A", kind="secondary")]),
            DiagramNode(node_id="B", label="B", node_family="heat exchanger", x=345, y=180, width=260, height=140, labels=[DiagramLabel(text="E-102", kind="primary"), DiagramLabel(text="Very Long Exchanger Service B", kind="secondary")]),
            DiagramNode(node_id="C", label="C", node_family="heat exchanger", x=610, y=180, width=260, height=140, labels=[DiagramLabel(text="E-103", kind="primary"), DiagramLabel(text="Very Long Exchanger Service C", kind="secondary")]),
            DiagramNode(node_id="D", label="D", node_family="heat exchanger", x=875, y=180, width=260, height=140, labels=[DiagramLabel(text="E-104", kind="primary"), DiagramLabel(text="Very Long Exchanger Service D", kind="secondary")]),
        ]
        modules = DiagramModuleArtifact(
            diagram_id="dense_modules",
            route_id="dense_route",
            module_kind=DiagramLevel.PFD,
            modules=[
                DiagramModuleSpec(module_id="m1", module_kind=DiagramLevel.PFD, title="A", symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY, entity_ids=["A"]),
                DiagramModuleSpec(module_id="m2", module_kind=DiagramLevel.PFD, title="B", symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY, entity_ids=["B"]),
                DiagramModuleSpec(module_id="m3", module_kind=DiagramLevel.PFD, title="C", symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY, entity_ids=["C"]),
                DiagramModuleSpec(module_id="m4", module_kind=DiagramLevel.PFD, title="D", symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY, entity_ids=["D"]),
            ],
            markdown="seed",
        )
        composition = DiagramSheetCompositionArtifact(
            diagram_id="dense_comp",
            route_id="dense_route",
            diagram_level=DiagramLevel.PFD,
            sheets=[
                DiagramSheetComposition(
                    sheet_id="sheet_1",
                    title="Process Flow Diagram",
                    diagram_level=DiagramLevel.PFD,
                    width_px=1200,
                    height_px=700,
                    module_placements=[
                        DiagramModulePlacement(module_id="m1", sheet_id="sheet_1", x=80, y=160, width=250, height=220),
                        DiagramModulePlacement(module_id="m2", sheet_id="sheet_1", x=345, y=160, width=250, height=220),
                        DiagramModulePlacement(module_id="m3", sheet_id="sheet_1", x=610, y=160, width=250, height=220),
                        DiagramModulePlacement(module_id="m4", sheet_id="sheet_1", x=875, y=160, width=250, height=220),
                    ],
                    connectors=[],
                )
            ],
            markdown="seed",
        )
        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id="dense_pfd",
            nodes=nodes,
            edges=[],
            sheets=sheets,
            modules=modules,
            sheet_composition=composition,
            target=target,
        )

        self.assertEqual(acceptance.overall_status, "conditional")
        self.assertGreaterEqual(acceptance.crowded_sheet_count, 1)
        self.assertLess(acceptance.benchmark_cleanliness_score, 1.0)

    def test_phase6_pfd_acceptance_marks_overlapping_case_blocked(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        sheets = [DiagramSheet(sheet_id="sheet_1", title="Process Flow Diagram", width_px=900, height_px=500, node_ids=["A", "B", "C"])]
        nodes = [
            DiagramNode(
                node_id="A",
                label="A",
                node_family="reactor",
                x=120,
                y=120,
                width=220,
                height=140,
                labels=[DiagramLabel(text="R-101", kind="primary"), DiagramLabel(text="Primary reactor duty", kind="secondary")],
            ),
            DiagramNode(
                node_id="B",
                label="B",
                node_family="reactor",
                x=210,
                y=160,
                width=220,
                height=140,
                labels=[DiagramLabel(text="R-102", kind="primary"), DiagramLabel(text="Primary reactor duty", kind="secondary")],
            ),
            DiagramNode(
                node_id="C",
                label="C",
                node_family="heat exchanger",
                x=300,
                y=195,
                width=220,
                height=120,
                labels=[DiagramLabel(text="E-101", kind="primary"), DiagramLabel(text="High duty exchanger", kind="secondary")],
            ),
        ]
        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id="blocked_pfd",
            nodes=nodes,
            edges=[],
            sheets=sheets,
            target=target,
        )

        self.assertEqual(acceptance.overall_status, "blocked")
        self.assertGreater(acceptance.node_overlap_count, 0)
        self.assertIn("diagram_node_overlap", acceptance.blocking_issue_codes)

    def test_phase14_pfd_acceptance_blocks_severe_route_congestion(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        sheets = [DiagramSheet(sheet_id="sheet_1", title="Process Flow Diagram", width_px=1200, height_px=700, node_ids=["A", "B"])]
        nodes = [
            DiagramNode(node_id="A", label="A", node_family="tank", x=140, y=220, width=220, height=140, labels=[DiagramLabel(text="TK-101", kind="primary")]),
            DiagramNode(node_id="B", label="B", node_family="reactor", x=760, y=220, width=220, height=140, labels=[DiagramLabel(text="R-101", kind="primary")]),
        ]
        routing = DiagramRoutingArtifact(
            diagram_id="route_quality",
            route_id="route_quality",
            diagram_level=DiagramLevel.PFD,
            sheets=[
                DiagramRoutingSheet(
                    sheet_id="sheet_1",
                    route_hints=[],
                    continuation_markers=[],
                    crossing_count=5,
                    congested_connector_count=3,
                    max_channel_load=5,
                )
            ],
            markdown="seed",
        )

        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id="route_quality",
            nodes=nodes,
            edges=[],
            sheets=sheets,
            routing=routing,
            target=target,
        )

        self.assertEqual(acceptance.overall_status, "blocked")
        self.assertIn("diagram_route_congestion", acceptance.warning_issue_codes)
        self.assertIn("diagram_route_crossings", acceptance.warning_issue_codes)
        self.assertIn("diagram_route_congestion_blocked", acceptance.blocking_issue_codes)
        self.assertLess(acceptance.benchmark_cleanliness_score, 1.0)

    def test_phase7_drawio_export_contains_pages_modules_and_edges(self):
        artifact, flowsheet_graph, flowsheet_case, stream_table, library, style, target, modules, composition = self._build_phase4_regression_artifact()
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        routing = build_process_flow_diagram_routing_artifact(semantics, modules, composition, artifact)
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="Process Flow Diagram",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
            routing=routing,
        )

        self.assertIn("<mxfile", drawio)
        self.assertIn('name="Process Flow Diagram"', drawio)
        self.assertIn("Feed Handling", drawio)
        self.assertIn("R-101", drawio)
        self.assertIn("To reactor", drawio)
        self.assertIn("orthogonalEdgeStyle", drawio)
        self.assertIn('<Array as="points">', drawio)
        self.assertIn("<mxPoint x=", drawio)

    def test_phase9_pfd_drawio_regression_signature_matches_fixture(self):
        artifact, _, _, _, _, _, _, modules, composition = self._build_phase4_regression_artifact()
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="Process Flow Diagram",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
        )

        expected = self._fixture_path("pfd_drawio_signature.txt").read_text()
        actual = self._drawio_regression_signature(drawio)
        self.assertEqual(actual, expected)

    def test_phase9_multi_sheet_pfd_benchmark_splits_and_exports_multiple_pages(self):
        section_nodes = [
            ("TK-501", "tank", "Feed Tank A", "feed_a"),
            ("E-501", "heat_exchanger", "Preheater A", "preheat_a"),
            ("R-501", "cstr", "Reactor A", "reaction_a"),
            ("V-501", "flash_vessel", "Flash Drum A", "recovery_a"),
            ("TK-502", "tank", "Feed Tank B", "feed_b"),
            ("E-502", "heat_exchanger", "Preheater B", "preheat_b"),
            ("R-502", "cstr", "Reactor B", "reaction_b"),
            ("C-502", "distillation_column", "Polishing Column B", "purification_b"),
        ]
        stream_specs = [
            ("S1", "Feed A", "", "TK-501", 25.0, 1.0),
            ("S2", "To preheater A", "TK-501", "E-501", 35.0, 1.2),
            ("S3", "To reactor A", "E-501", "R-501", 60.0, 2.0),
            ("S4", "To recovery A", "R-501", "V-501", 88.0, 2.4),
            ("S5", "Feed B", "", "TK-502", 25.0, 1.0),
            ("S6", "To preheater B", "TK-502", "E-502", 35.0, 1.2),
            ("S7", "To reactor B", "E-502", "R-502", 60.0, 2.0),
            ("S8", "To column B", "R-502", "C-502", 92.0, 2.6),
        ]
        acceptance, composition, artifact, modules = self._build_pfd_acceptance_for_case(
            case_id="multi_sheet_parallel_trains",
            section_nodes=section_nodes,
            stream_specs=stream_specs,
        )
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="Process Flow Diagram",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
        )

        self.assertIn(acceptance.overall_status, {"complete", "conditional"})
        self.assertNotEqual(acceptance.overall_status, "blocked")
        self.assertGreater(len(composition.sheets), 1)
        self.assertGreater(len(artifact.sheets), 1)
        self.assertGreater(drawio.count("<diagram "), 1)

    def test_phase5_curated_pfd_benchmark_set_meets_cleanliness_gate(self):
        benchmark_cases = [
            {
                "name": "linear_liquid_train",
                "section_nodes": [
                    ("TK-101", "tank", "Feed Tank", "feed"),
                    ("R-101", "cstr", "Reactor", "reaction"),
                    ("C-101", "distillation_column", "Column", "purification"),
                ],
                "stream_specs": [
                    ("S1", "Fresh feed", "", "TK-101", 25.0, 1.0),
                    ("S2", "To reactor", "TK-101", "R-101", 40.0, 2.0),
                    ("S3", "To column", "R-101", "C-101", 80.0, 2.5),
                ],
            },
            {
                "name": "mixed_height_reaction_recovery",
                "section_nodes": [
                    ("R-101", "cstr", "Primary Reactor", "reaction"),
                    ("E-101", "heat_exchanger", "Feed Effluent Exchanger", "reaction"),
                    ("P-101", "pump", "Recycle Pump", "reaction"),
                    ("V-101", "flash_vessel", "Flash Drum", "recovery"),
                ],
                "stream_specs": [
                    ("S1", "Feed", "", "R-101", 30.0, 1.2),
                    ("S2", "Hot effluent", "R-101", "E-101", 95.0, 3.1),
                    ("S3", "Recycle leg", "E-101", "P-101", 60.0, 2.8),
                    ("S4", "To flash", "P-101", "V-101", 55.0, 2.2),
                ],
            },
            {
                "name": "wide_exchange_purification_train",
                "section_nodes": [
                    ("E-201", "heat_exchanger", "Feed Effluent Exchanger Train A", "exchange"),
                    ("E-202", "heat_exchanger", "Product Cooler Train B", "exchange"),
                    ("C-201", "distillation_column", "Polishing Column", "purification"),
                    ("TK-201", "tank", "Product Tank", "storage"),
                ],
                "stream_specs": [
                    ("S1", "Feed", "", "E-201", 25.0, 1.0),
                    ("S2", "Preheated feed", "E-201", "E-202", 65.0, 2.3),
                    ("S3", "To polishing", "E-202", "C-201", 75.0, 2.0),
                    ("S4", "To storage", "C-201", "TK-201", 35.0, 1.1),
                ],
            },
            {
                "name": "recycle_heavy_reaction_train",
                "section_nodes": [
                    ("R-301", "cstr", "Loop Reactor", "reaction"),
                    ("E-301", "heat_exchanger", "Recycle Cooler", "reaction"),
                    ("P-301", "pump", "Recycle Pump", "reaction"),
                    ("C-301", "distillation_column", "Recovery Column", "purification"),
                ],
                "stream_specs": [
                    ("S1", "Fresh feed", "", "R-301", 25.0, 1.0),
                    ("S2", "Reactor effluent", "R-301", "E-301", 90.0, 2.8),
                    ("S3", "Recycle circulation", "E-301", "P-301", 55.0, 2.4),
                    ("S4", "Forward flow", "P-301", "C-301", 60.0, 2.2),
                ],
            },
            {
                "name": "utility_dense_conditioned_train",
                "section_nodes": [
                    ("TK-401", "tank", "Conditioned Feed Tank", "feed"),
                    ("E-401", "heat_exchanger", "Feed Heater", "conditioning"),
                    ("R-401", "cstr", "Conditioned Reactor", "reaction"),
                    ("TK-402", "tank", "Hold Tank", "storage"),
                ],
                "stream_specs": [
                    ("S1", "Chilled feed", "", "TK-401", 12.0, 1.0),
                    ("S2", "Heated feed", "TK-401", "E-401", 45.0, 2.0),
                    ("S3", "Conditioned feed", "E-401", "R-401", 70.0, 2.4),
                    ("S4", "Product hold", "R-401", "TK-402", 38.0, 1.2),
                ],
            },
        ]

        for case in benchmark_cases:
            with self.subTest(case=case["name"]):
                acceptance, composition, artifact, _modules = self._build_pfd_acceptance_for_case(
                    case_id=case["name"],
                    section_nodes=case["section_nodes"],
                    stream_specs=case["stream_specs"],
                )
                self.assertEqual(acceptance.overall_status, "complete")
                self.assertEqual(acceptance.node_overlap_count, 0)
                self.assertEqual(acceptance.node_label_overlap_count, 0)
                self.assertLessEqual(acceptance.crowded_sheet_count, 1)
                self.assertGreaterEqual(acceptance.benchmark_cleanliness_score, 0.72)
                self.assertGreaterEqual(len(composition.sheets), 1)
                self.assertGreaterEqual(len(artifact.sheets), 1)

    def test_control_phase3_builders_emit_semantics_modules_and_composition(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_ctrl",
            route_id="route_ctrl",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="C-101", unit_type="distillation_column", label="Column", section_id="purification"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification"],
            stream_ids=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Temperature",
                    manipulated_variable="Coolant flow",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="Open cooling gradually",
                    shutdown_logic="Close feed and cool",
                    override_logic="High-high trip override",
                    safeguard_linkage="Reactor HH temperature interlock",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_architecture = ControlArchitectureDecision(
            decision=DecisionRecord(
                decision_id="control_architecture",
                context="seed",
                selected_candidate_id="cascade_override",
                selected_summary="seed",
                citations=["s1"],
                assumptions=["seed"],
            ),
            critical_units=["R-101"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_control_system_semantics(control_plan, control_architecture, flowsheet_graph, library)
        modules = build_control_system_modules(semantics, library)
        composition = build_control_system_sheet_composition(modules, style)

        self.assertGreaterEqual(len(semantics.entities), 3)
        self.assertTrue(any(entity.kind.value == "control_loop" for entity in semantics.entities))
        self.assertEqual(len(modules.modules), 1)
        self.assertEqual(len(composition.sheets), 4)
        self.assertEqual(composition.sheets[2].title, "Interlocks and Permissives")
        self.assertEqual(composition.sheets[3].title, "Shutdowns and Protective Trips")

        review = build_control_cause_effect_artifact(control_plan, control_architecture, flowsheet_graph)
        self.assertEqual(len(review.rows), 1)
        self.assertEqual(review.rows[0].control_id, "TIC-101")
        self.assertTrue(review.rows[0].safety_critical)
        self.assertEqual(review.rows[0].protected_final_action, "Coolant flow")

    def test_control_renderer_uses_composition_artifacts(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_ctrl_render",
            route_id="route_ctrl_render",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="E-101", unit_type="heat_exchanger", label="Cooler", section_id="reaction"),
            ],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Temperature",
                    manipulated_variable="Coolant flow",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="Open cooling gradually",
                    shutdown_logic="Close feed and cool",
                    override_logic="High-high trip override",
                    safeguard_linkage="Reactor HH temperature interlock",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                ControlLoop(
                    control_id="FIC-201",
                    unit_id="E-101",
                    loop_family="flow",
                    controlled_variable="Coolant flow",
                    manipulated_variable="Cooling water valve",
                    sensor="FT-201",
                    actuator="FV-201",
                    objective="Maintain cooler duty",
                    startup_logic="Open utility line gradually",
                    shutdown_logic="Close utility valve",
                    override_logic="Manual bypass during startup",
                    safeguard_linkage="Low-flow alarm",
                    criticality="medium",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_architecture = ControlArchitectureDecision(
            decision=DecisionRecord(
                decision_id="control_architecture",
                context="seed",
                selected_candidate_id="cascade_override",
                selected_summary="seed",
                citations=["s1"],
                assumptions=["seed"],
            ),
            critical_units=["R-101", "E-101"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_control_system_semantics(control_plan, control_architecture, flowsheet_graph, library)
        modules = build_control_system_modules(semantics, library)
        composition = build_control_system_sheet_composition(modules, style)
        composition.sheets[0].width_px = 2100

        artifact = build_control_system_diagram(
            control_plan,
            control_architecture,
            flowsheet_graph,
            style,
            None,
            semantics,
            modules,
            composition,
        )
        routing = build_control_system_routing_artifact(
            control_plan,
            control_architecture,
            flowsheet_graph,
            style,
            modules,
            composition,
            artifact,
        )
        artifact = build_control_system_diagram(
            control_plan,
            control_architecture,
            flowsheet_graph,
            style,
            None,
            semantics,
            modules,
            composition,
            routing,
        )

        self.assertEqual(artifact.sheets[0].width_px, 2100)
        self.assertIn("Process Control Architecture", artifact.sheets[0].svg)
        self.assertIn("stroke-dasharray='8,6'", artifact.sheets[0].svg)
        self.assertEqual(len(artifact.sheets), 4)
        self.assertEqual(routing.diagram_level, DiagramLevel.CONTROL)
        self.assertTrue(any(sheet.sheet_id == "sheet_2" for sheet in routing.sheets))
        self.assertGreaterEqual(sum(len(sheet.route_hints) for sheet in routing.sheets), 1)
        self.assertEqual(artifact.sheets[2].title, "Interlocks and Permissives")
        self.assertIn("Cause / permissive", artifact.sheets[2].svg)
        self.assertIn("Action / shutdown", artifact.sheets[2].svg)
        self.assertIn("Override", artifact.sheets[2].svg)
        self.assertIn("Safeguard / trip", artifact.sheets[2].svg)
        self.assertIn("Criticality:", artifact.sheets[2].svg)
        self.assertIn("Reactor HH", artifact.sheets[2].svg)
        self.assertIn("temperature", artifact.sheets[2].svg)
        self.assertIn("interlock", artifact.sheets[2].svg)
        self.assertIn("Protective", artifact.sheets[2].svg)
        self.assertIn("trip /", artifact.sheets[2].svg)
        self.assertEqual(artifact.sheets[3].title, "Shutdowns and Protective Trips")
        self.assertIn("Trip cause:", artifact.sheets[3].svg)
        self.assertIn("Shutdown action:", artifact.sheets[3].svg)
        self.assertIn("Protected final action:", artifact.sheets[3].svg)

        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="Control System Diagram",
            sheets=artifact.sheets,
            modules=modules,
            sheet_composition=composition,
            routing=routing,
            control_plan=control_plan,
        )
        self.assertIn('name="Interlocks and Permissives"', drawio)
        self.assertIn('name="Shutdowns and Protective Trips"', drawio)
        self.assertIn("CONTROL REVIEW", drawio)
        self.assertIn("SHUTDOWN REVIEW", drawio)
        self.assertIn("Cause / permissive", drawio)
        self.assertIn("Trip cause", drawio)
        self.assertIn("Protected final action", drawio)
        self.assertIn("TIC-101", drawio)
        self.assertIn("High-high trip override", drawio)
        self.assertIn("Close feed and cool", drawio)
        self.assertIn('<Array as="points">', drawio)

    def test_phase11_pid_lite_builders_create_isolated_unit_clusters(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid",
            route_id="route_pid",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="V-101", unit_type="separator", label="Separator", section_id="cleanup"),
            ],
            unit_models=[],
            section_ids=["reaction", "cleanup"],
            stream_ids=["S-201", "S-301"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    destination_unit_id="V-101",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S-301",
                    description="Product transfer",
                    temperature_c=55.0,
                    pressure_bar=1.4,
                    components=[StreamComponentFlow(name="P", mass_flow_kg_hr=9.0, molar_flow_kmol_hr=0.08)],
                    source_unit_id="V-101",
                    stream_role="product",
                    section_id="cleanup",
                ),
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Coolant valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor HH temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                ControlLoop(
                    control_id="LIC-301",
                    unit_id="V-101",
                    loop_family="level",
                    controlled_variable="Separator level",
                    manipulated_variable="Product discharge valve",
                    sensor="LT-301",
                    actuator="LV-301",
                    objective="Maintain separator level",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="",
                    criticality="medium",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)

        self.assertEqual(semantics.diagram_id, "route_pid_pid_lite_semantics")
        self.assertEqual(len(modules.modules), 2)
        self.assertEqual(len(composition.sheets), 2)
        self.assertTrue(all(module.must_be_isolated for module in modules.modules))
        self.assertTrue(any(entity.symbol_key == "pid_controller" for entity in semantics.entities))
        self.assertTrue(any(entity.symbol_key == "pid_relief_valve" for entity in semantics.entities))
        self.assertTrue(any(connection.line_class == "process_liquid" for connection in semantics.connections if connection.role == DiagramEdgeRole.PROCESS))

    def test_phase11_pid_lite_builders_pass_validation_contract(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_valid",
            route_id="route_pid_valid",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)

        self.assertFalse(validate_plant_diagram_semantics(semantics))
        self.assertFalse(validate_diagram_semantics_against_symbol_library(semantics, library))
        self.assertFalse(validate_diagram_module_artifact(modules, semantics))
        self.assertFalse(validate_diagram_module_symbols_against_library(modules, semantics, library))
        self.assertEqual(composition.sheets[0].diagram_level, DiagramLevel.PID_LITE)

    def test_phase11_pid_lite_renderer_outputs_svg_and_drawio(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_render",
            route_id="route_pid_render",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Coolant valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor HH temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        seed = build_pid_lite_diagram(
            flowsheet_graph,
            stream_table,
            control_plan,
            style,
            semantics,
            modules,
            composition,
        )
        routing = build_pid_lite_routing_artifact(semantics, modules, composition, seed)
        artifact = build_pid_lite_diagram(
            flowsheet_graph,
            stream_table,
            control_plan,
            style,
            semantics,
            modules,
            composition,
            routing,
        )
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="P&ID-lite",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
            routing=routing,
        )

        self.assertEqual(len(artifact.sheets), 1)
        self.assertEqual(len(routing.sheets), 1)
        self.assertGreaterEqual(len(routing.sheets[0].route_hints), 3)
        self.assertIn("P&amp;ID-lite", artifact.sheets[0].svg)
        self.assertIn("stroke='#8b1e3f'", artifact.sheets[0].svg)
        self.assertIn("stroke='#c2410c'", artifact.sheets[0].svg)
        self.assertIn("<circle", artifact.sheets[0].svg)
        self.assertIn("<polygon", artifact.sheets[0].svg)
        self.assertIn("Coolant valve", drawio)
        self.assertIn("TT-101", drawio)
        self.assertIn("edgeStyle=orthogonalEdgeStyle", drawio)
        self.assertIn('<Array as="points">', drawio)

    def test_phase12_pid_lite_layout_places_attachments_by_role(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_phase12",
            route_id="route_pid_phase12",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Coolant valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor HH temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)

        node_map = {node.node_id: node for node in artifact.nodes}
        unit = next(node for node in artifact.nodes if node.equipment_tag == "R-101")
        transmitter = next(node for node in artifact.nodes if node.equipment_tag == "TT-101")
        controller = next(node for node in artifact.nodes if node.equipment_tag == "TIC-101")
        control_valve = next(node for node in artifact.nodes if node.equipment_tag == "TV-101")
        relief = next(node for node in artifact.nodes if node.equipment_tag == "PSV-001")

        self.assertLess(transmitter.x + transmitter.width / 2, unit.x + unit.width / 2)
        self.assertLess(controller.y + controller.height / 2, unit.y + unit.height / 2)
        self.assertGreater(control_valve.x + control_valve.width / 2, unit.x + unit.width / 2)
        self.assertLess(relief.y + relief.height / 2, unit.y + unit.height / 2)
        self.assertIn(unit.node_id, node_map)

    def test_phase12_pid_lite_route_hints_use_role_aware_corridors(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_routes",
            route_id="route_pid_routes",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)

        entity_lookup = {entity.entity_id: entity for entity in semantics.entities}
        route_hints = _build_pid_lite_route_hints(
            artifact.sheets[0].sheet_id,
            artifact.edges,
            artifact.nodes,
            {
                node.node_id: entity_lookup[node.node_id.split("__", 1)[1]]
                for node in artifact.nodes
                if "__" in node.node_id and node.node_id.split("__", 1)[1] in entity_lookup
            },
        )
        signal_edge = next(edge for edge in artifact.edges if edge.edge_type == "control_signal")
        safeguard_edge = next(edge for edge in artifact.edges if edge.edge_type == "safeguard")
        process_edge = next(edge for edge in artifact.edges if edge.edge_type == "main" and edge.stream_id)

        signal_points = route_hints[signal_edge.edge_id]["points"]
        safeguard_points = route_hints[safeguard_edge.edge_id]["points"]
        process_points = route_hints[process_edge.edge_id]["points"]

        self.assertEqual(signal_points[1][1], signal_points[2][1])
        self.assertLess(signal_points[1][1], min(signal_points[0][1], signal_points[-1][1]))
        self.assertEqual(safeguard_points[1][1], safeguard_points[2][1])
        self.assertLess(safeguard_points[1][1], min(safeguard_points[0][1], safeguard_points[-1][1]))
        self.assertEqual(process_points[1][1], process_points[2][1])
        self.assertGreater(process_points[1][1], max(process_points[0][1], process_points[-1][1]))

    def test_phase12_pid_lite_column_uses_family_specific_anchor_sides(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_column",
            route_id="route_pid_column",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="C-101", unit_type="distillation_column", label="Column", section_id="purification")],
            unit_models=[],
            section_ids=["purification"],
            stream_ids=["S-401"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-401",
                    description="Column bottoms",
                    temperature_c=95.0,
                    pressure_bar=1.8,
                    components=[StreamComponentFlow(name="P", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.07)],
                    source_unit_id="C-101",
                    stream_role="product",
                    section_id="purification",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="LIC-401",
                    unit_id="C-101",
                    loop_family="level",
                    controlled_variable="Bottoms level",
                    manipulated_variable="Bottoms valve",
                    sensor="LT-401",
                    actuator="LV-401",
                    objective="Maintain bottoms level",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="",
                    criticality="medium",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)

        unit = next(node for node in artifact.nodes if node.equipment_tag == "C-101")
        transmitter = next(node for node in artifact.nodes if node.equipment_tag == "LT-401")
        control_valve = next(node for node in artifact.nodes if node.equipment_tag == "LV-401")
        line_valve = next(node for node in artifact.nodes if "attachment_role=process_line" in node.notes)
        unit_entity = next(entity for entity in semantics.entities if entity.unit_id == "C-101")

        self.assertEqual(unit_entity.metadata.get("template_family"), "column")
        self.assertEqual(unit.node_family, "column")
        self.assertIn("pid_attach_side=left", transmitter.notes)
        self.assertIn("pid_attach_side=right", control_valve.notes)
        self.assertIn("pid_attach_side=top", line_valve.notes)
        self.assertLess(transmitter.x + transmitter.width / 2, unit.x + unit.width / 2)
        self.assertGreater(control_valve.x + control_valve.width / 2, unit.x + unit.width / 2)
        self.assertGreater(line_valve.y + line_valve.height / 2, unit.y + unit.height / 2)

    def test_phase12_pid_lite_dense_same_side_attachments_fan_out(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_dense",
            route_id="route_pid_dense",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_loops = []
        for idx in range(1, 6):
            control_loops.append(
                ControlLoop(
                    control_id=f"TIC-{100+idx}",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable=f"Zone {idx} temperature",
                    manipulated_variable=f"Coolant valve {idx}",
                    sensor=f"TT-{100+idx}",
                    actuator=f"TV-{100+idx}",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="",
                    criticality="medium",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            )
        control_plan = ControlPlanArtifact(
            control_loops=control_loops,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)

        transmitters = [node for node in artifact.nodes if node.equipment_tag.startswith("TT-")]
        control_valves = [node for node in artifact.nodes if node.equipment_tag.startswith("TV-")]
        self.assertGreaterEqual(len(transmitters), 5)
        self.assertGreaterEqual(len(control_valves), 5)

        transmitter_xs = {round(node.x, 1) for node in transmitters}
        transmitter_ys = {round(node.y, 1) for node in transmitters}
        valve_xs = {round(node.x, 1) for node in control_valves}
        valve_ys = {round(node.y, 1) for node in control_valves}

        self.assertGreater(len(transmitter_ys), 1)
        self.assertGreater(len(valve_ys), 1)
        self.assertTrue(len(transmitter_xs) > 1 or len(artifact.sheets) > 1)
        self.assertTrue(len(valve_xs) > 1 or len(artifact.sheets) > 1)

    def test_phase12_pid_lite_svg_uses_tighter_non_overlapping_edge_callouts(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_labels",
            route_id="route_pid_labels",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Coolant valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor HH temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                ControlLoop(
                    control_id="PIC-102",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-102",
                    actuator="PV-102",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style)
        svg = artifact.sheets[0].svg

        self.assertIn("Process Liquid", svg)
        self.assertTrue("Line Control" in svg or "Final Control" in svg)
        self.assertIn("Pressure", svg)
        self.assertIn("Relief Valve", svg)
        self.assertGreaterEqual(svg.count("stroke='#d0d7de'"), 4)

    def test_phase12_pid_lite_splits_dense_unit_cluster_into_multiple_views(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_split",
            route_id="route_pid_split",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_loops = []
        for idx in range(1, 5):
            control_loops.append(
                ControlLoop(
                    control_id=f"TIC-{110+idx}",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable=f"Zone {idx} temperature",
                    manipulated_variable=f"Coolant valve {idx}",
                    sensor=f"TT-{110+idx}",
                    actuator=f"TV-{110+idx}",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="High-high temperature trip" if idx % 2 == 0 else "",
                    criticality="medium",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            )
        control_plan = ControlPlanArtifact(
            control_loops=control_loops,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)

        self.assertGreater(len(modules.modules), 1)
        self.assertEqual(len(composition.sheets), len(modules.modules))
        self.assertEqual(len(artifact.sheets), len(modules.modules))
        self.assertTrue(all("(View " in module.title for module in modules.modules))
        self.assertTrue(all(any("Split view" in note for note in module.notes) for module in modules.modules))
        self.assertEqual(sum(1 for node in artifact.nodes if node.equipment_tag == "R-101"), len(artifact.sheets))

    def test_phase12_pid_lite_svg_includes_local_legend_disciplines(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_legend",
            route_id="route_pid_legend",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Coolant valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor HH temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style)
        svg = artifact.sheets[0].svg

        self.assertIn("P&amp;ID-LITE LEGEND", svg)
        self.assertIn("Line Classes", svg)
        self.assertIn("Loop Tags", svg)
        self.assertIn("Symbols", svg)
        self.assertIn("Process Liquid", svg)
        self.assertIn("TIC-101", svg)
        self.assertIn("Instrument bubble", svg)
        self.assertIn("Valve / final element", svg)

    def test_phase12_pid_lite_drawio_includes_local_legend_disciplines(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_legend_drawio",
            route_id="route_pid_legend_drawio",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    loop_family="temperature",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Coolant valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor HH temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="P&ID-lite",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
        )

        self.assertIn("P&amp;ID-LITE LEGEND", drawio)
        self.assertIn("Line Classes", drawio)
        self.assertIn("Loop Tags", drawio)
        self.assertIn("Symbols", drawio)
        self.assertIn("Process Liquid", drawio)
        self.assertIn("TIC-101", drawio)
        self.assertIn("Instrument bubble", drawio)
        self.assertIn("Valve / final element", drawio)

    def test_phase12_pid_lite_drawio_uses_attachment_side_geometry(self):
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_pid_drawio_ports",
            route_id="route_pid_drawio_ports",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="C-101", unit_type="distillation_column", label="Column", section_id="purification")],
            unit_models=[],
            section_ids=["purification"],
            stream_ids=["S-301"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-301",
                    description="Column bottoms",
                    temperature_c=110.0,
                    pressure_bar=1.7,
                    components=[StreamComponentFlow(name="C", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="C-101",
                    stream_role="product",
                    section_id="purification",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-301",
                    unit_id="C-101",
                    loop_family="pressure",
                    controlled_variable="Column pressure",
                    manipulated_variable="Overhead valve",
                    sensor="PT-301",
                    actuator="PV-301",
                    objective="Maintain column pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library)
        modules = build_pid_lite_modules(semantics, library)
        composition = build_pid_lite_sheet_composition(modules, style)
        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, semantics, modules, composition)
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="P&ID-lite",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
        )

        self.assertIn("exitX=0.0;exitY=0.5;exitPerimeter=0;", drawio)
        self.assertIn("entryX=1.0;entryY=0.5;entryPerimeter=0;", drawio)
        self.assertIn("entryX=0.5;entryY=0.0;entryPerimeter=0;", drawio)

    def test_phase12_edge_label_resolution_avoids_prior_edge_label_obstacles(self):
        nodes = []
        sheet = DiagramSheet(sheet_id="sheet_1", title="Reactor P&ID-lite Cluster", width_px=900, height_px=700)
        first_rect = _label_bounds(360.0, 180.0, "Reactor temperature", 20, 10)
        resolved_x, resolved_y = _resolve_edge_label_position(
            360.0,
            180.0,
            "Coolant valve",
            20,
            10,
            nodes,
            sheet=sheet,
            route_points=[(320.0, 220.0), (320.0, 180.0), (400.0, 180.0), (400.0, 220.0)],
            obstacle_rects=[first_rect],
        )
        second_rect = _label_bounds(resolved_x, resolved_y, "Coolant valve", 20, 10)

        self.assertFalse(_rectangles_overlap(first_rect, second_rect, padding=4.0))

    def test_phase17_drafting_metadata_renders_in_svg_and_drawio(self):
        style = build_diagram_style_profile()
        sheets = [
            DiagramSheet(sheet_id="sheet_1", title="Process Flow Diagram", width_px=900, height_px=500),
            DiagramSheet(sheet_id="sheet_2", title="Process Flow Diagram", width_px=900, height_px=500),
        ]

        apply_diagram_drafting_metadata(sheets, drawing_prefix="route-pfd")
        svg = _render_svg(sheets[0], [], [], style)
        drawio = build_drawio_document(diagram_id="route_pfd", title="PFD", sheets=sheets, nodes=[], edges=[])

        self.assertEqual("ROUTE-PFD-001", sheets[0].drawing_number)
        self.assertEqual("1 of 2", sheets[0].sheet_number)
        self.assertIn("DRAFTING TITLE BLOCK", svg)
        self.assertIn("ROUTE-PFD-001", svg)
        self.assertIn("1 of 2", svg)
        self.assertIn("DRAFTING TITLE BLOCK", drawio)
        self.assertIn("ROUTE-PFD-002", drawio)

    def test_phase18_acceptance_blocks_bad_drafting_identity_and_title_block_overlap(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Demo Product", capacity_tpa=1000, target_purity_wt_pct=99.0))
        sheets = [
            DiagramSheet(
                sheet_id="sheet_1",
                title="Process Flow Diagram",
                width_px=900,
                height_px=500,
                drawing_number="PFD-001",
                sheet_number="1 of 2",
                revision_date="2026-04-12",
                node_ids=["A"],
                svg="<svg><text>No controlled title block</text></svg>",
            ),
            DiagramSheet(
                sheet_id="sheet_2",
                title="Process Flow Diagram",
                width_px=900,
                height_px=500,
                drawing_number="PFD-001",
                sheet_number="1 of 2",
                revision_date="2026-04-12",
                svg="<svg><text>DRAFTING TITLE BLOCK</text></svg>",
            ),
        ]
        nodes = [DiagramNode(node_id="A", label="A", node_family="reactor", x=470, y=395, width=160, height=80)]

        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id="bad_drafting_pfd",
            nodes=nodes,
            edges=[],
            sheets=sheets,
            target=target,
        )

        self.assertEqual(acceptance.overall_status, "blocked")
        self.assertEqual(acceptance.duplicate_drawing_number_count, 1)
        self.assertEqual(acceptance.duplicate_sheet_number_count, 1)
        self.assertEqual(acceptance.missing_title_block_count, 1)
        self.assertEqual(acceptance.title_block_overlap_count, 1)
        self.assertIn("diagram_drafting_identity_duplicate", acceptance.blocking_issue_codes)
        self.assertIn("diagram_title_block_missing", acceptance.blocking_issue_codes)
        self.assertIn("diagram_title_block_overlap", acceptance.blocking_issue_codes)

    def test_phase19_bac_pfd_suppresses_loop_ids_and_utility_duty_labels(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_phase19",
            route_id="route_bac_phase19",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", label="Main Reactor", unit_type="cstr", section_id="reaction", section_type="reaction")],
            section_ids=["reaction"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_bac_phase19",
            route_id="route_bac_phase19",
            operating_mode="continuous",
            units=[],
            streams=[StreamSpec(stream_id="S1", destination_unit_id="R-101", stream_role="feed", section_id="reaction")],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S1",
                    description="BAC feed",
                    destination_unit_id="R-101",
                    stream_role="feed",
                    section_id="reaction",
                    temperature_c=30.0,
                    pressure_bar=1.2,
                    components=[],
                )
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            route_id="route_bac_phase19",
            control_loops=[
                ControlLoop(
                    control_id="TIC-101",
                    unit_id="R-101",
                    controlled_variable="Reactor temperature",
                    manipulated_variable="Steam valve",
                    sensor="TT-101",
                    actuator="TV-101",
                    objective="Maintain reactor temperature",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="High temperature trip",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        energy_balance = EnergyBalance(
            duties=[UnitDuty(unit_id="R-101", heating_kw=250.0)],
            total_heating_kw=250.0,
            total_cooling_kw=0.0,
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_process_flow_diagram(
            flowsheet_graph,
            flowsheet_case,
            stream_table,
            None,
            energy_balance,
            style,
            target,
            control_plan,
        )
        reactor = next(node for node in artifact.nodes if node.node_id == "R-101")
        label_texts = [label.text for label in reactor.labels]

        self.assertFalse(any("TIC-101" in text for text in label_texts))
        self.assertFalse(any("kW heat" in text for text in label_texts))
        self.assertIn("suppressed_loop_ids=TIC-101", reactor.notes)
        self.assertIn("suppressed_utility_note=+250 kW heat", reactor.notes)

    def test_phase20_bac_bfd_uses_locked_section_order_and_labels(self):
        blueprint = FlowsheetBlueprintArtifact(
            blueprint_id="bp_bac_bfd_locked",
            route_id="bac_bfd_locked",
            route_name="BAC Route",
            steps=[
                FlowsheetBlueprintStep(
                    step_id="step_cleanup",
                    route_id="bac_bfd_locked",
                    section_id="cleanup",
                    section_label="flash cleanup",
                    step_role="cleanup",
                    unit_id="cleanup_drum",
                    unit_type="flash_vessel",
                    service="cleanup",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                FlowsheetBlueprintStep(
                    step_id="step_rxn",
                    route_id="bac_bfd_locked",
                    section_id="reaction",
                    section_label="quaternization",
                    step_role="reaction",
                    unit_id="reactor",
                    unit_type="cstr",
                    service="reaction",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                FlowsheetBlueprintStep(
                    step_id="step_feed",
                    route_id="bac_bfd_locked",
                    section_id="feed_prep",
                    section_label="feed charging",
                    step_role="feed_preparation",
                    unit_id="premix",
                    unit_type="feed_preparation",
                    service="feed preparation",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
                FlowsheetBlueprintStep(
                    step_id="step_storage",
                    route_id="bac_bfd_locked",
                    section_id="storage",
                    section_label="product tankage",
                    step_role="storage",
                    unit_id="tank_farm",
                    unit_type="storage_tank",
                    service="storage",
                    citations=["s1"],
                    assumptions=["seed"],
                ),
            ],
            recycle_intents=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()

        semantics = build_block_flow_diagram_semantics(blueprint, target, library)
        artifact = build_block_flow_diagram(blueprint, style, target)

        self.assertEqual(
            semantics.section_order,
            ["feed preparation", "reaction", "cleanup", "concentration", "purification", "storage", "waste handling"],
        )
        self.assertEqual([node.section_id for node in artifact.nodes[:7]], semantics.section_order)
        self.assertEqual(
            [node.labels[0].text for node in artifact.nodes[:7]],
            [
                "Feed Preparation",
                "Quaternization Reaction",
                "Primary Cleanup",
                "Concentration",
                "Purification",
                "Product Storage",
                "Waste Handling",
            ],
        )
        expected = self._fixture_path("bac_bfd_signature.txt").read_text()
        actual = self._bac_bfd_svg_signature(artifact)
        self.assertEqual(actual, expected)

    def test_phase21_bac_pfd_signature_matches_fixture(self):
        artifact = self._build_bac_pfd_regression_artifact()
        expected = self._fixture_path("bac_pfd_signature.txt").read_text()
        actual = self._bac_pfd_svg_signature(artifact)

        self.assertEqual(actual, expected)

    def test_phase21_bac_pfd_acceptance_keeps_clean_sheet_complete(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        sheets = [DiagramSheet(sheet_id="sheet_1", title="Process Flow Diagram", width_px=1000, height_px=1000, node_ids=["reactor"])]
        apply_diagram_drafting_metadata(sheets, drawing_prefix="bac-clean-pfd")
        nodes = [DiagramNode(node_id="reactor", label="Reactor", node_family="bac_reactor", x=220, y=220, width=220, height=160, labels=[DiagramLabel(text="R-101", kind="primary"), DiagramLabel(text="Jacketed CSTR Reactor", kind="secondary")])]
        modules = DiagramModuleArtifact(
            diagram_id="bac_clean_modules",
            route_id="bac_clean_route",
            module_kind=DiagramLevel.PFD,
            modules=[DiagramModuleSpec(module_id="m1", module_kind=DiagramLevel.PFD, title="Reaction", symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY, entity_ids=["reactor"])],
            markdown="seed",
        )
        composition = DiagramSheetCompositionArtifact(
            diagram_id="bac_clean_comp",
            route_id="bac_clean_route",
            diagram_level=DiagramLevel.PFD,
            sheets=[DiagramSheetComposition(sheet_id="sheet_1", title="Process Flow Diagram", diagram_level=DiagramLevel.PFD, width_px=1000, height_px=1000, module_placements=[DiagramModulePlacement(module_id="m1", sheet_id="sheet_1", x=160, y=180, width=420, height=420)], connectors=[])],
            markdown="seed",
        )

        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id="bac_clean_pfd",
            nodes=nodes,
            edges=[],
            sheets=sheets,
            modules=modules,
            sheet_composition=composition,
            target=target,
        )

        self.assertEqual(acceptance.overall_status, "complete")
        self.assertNotIn("bac_pfd_cleanliness_below_target", acceptance.warning_issue_codes)

    def test_phase21_bac_pfd_acceptance_marks_marginal_density_conditional(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        sheets = [DiagramSheet(sheet_id="sheet_1", title="Process Flow Diagram", width_px=1000, height_px=1000, node_ids=["reactor"])]
        apply_diagram_drafting_metadata(sheets, drawing_prefix="bac-dense-pfd")
        nodes = [DiagramNode(node_id="reactor", label="Reactor", node_family="bac_reactor", x=260, y=260, width=220, height=160, labels=[DiagramLabel(text="R-101", kind="primary"), DiagramLabel(text="Jacketed CSTR Reactor", kind="secondary")])]
        modules = DiagramModuleArtifact(
            diagram_id="bac_dense_modules",
            route_id="bac_dense_route",
            module_kind=DiagramLevel.PFD,
            modules=[DiagramModuleSpec(module_id="m1", module_kind=DiagramLevel.PFD, title="Reaction", symbol_policy=DiagramSymbolPolicy.PROCESS_ONLY, entity_ids=["reactor"])],
            markdown="seed",
        )
        composition = DiagramSheetCompositionArtifact(
            diagram_id="bac_dense_comp",
            route_id="bac_dense_route",
            diagram_level=DiagramLevel.PFD,
            sheets=[DiagramSheetComposition(sheet_id="sheet_1", title="Process Flow Diagram", diagram_level=DiagramLevel.PFD, width_px=1000, height_px=1000, module_placements=[DiagramModulePlacement(module_id="m1", sheet_id="sheet_1", x=70, y=70, width=860, height=860)], connectors=[])],
            markdown="seed",
        )

        acceptance = build_diagram_acceptance(
            diagram_kind="pfd",
            diagram_id="bac_dense_pfd",
            nodes=nodes,
            edges=[],
            sheets=sheets,
            modules=modules,
            sheet_composition=composition,
            target=target,
        )

        self.assertEqual(acceptance.overall_status, "conditional")
        self.assertIn("bac_pfd_cleanliness_below_target", acceptance.warning_issue_codes)
        self.assertGreaterEqual(acceptance.benchmark_cleanliness_score, 0.72)

    def test_phase22_bac_pid_semantics_adds_clusters_for_sparse_critical_units(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_phase22",
            route_id="route_bac_pid_phase22",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="PU-201", unit_type="distillation_column", label="Purification Column", section_id="purification"),
                FlowsheetNode(node_id="TK-301", unit_type="tank", label="Product Storage Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification", "storage"],
            stream_ids=["S-201", "S-401", "S-402"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(stream_id="S-201", description="Reactor effluent", source_unit_id="R-101", destination_unit_id="PU-201", stream_role="intermediate", section_id="reaction", temperature_c=85.0, pressure_bar=2.8, components=[]),
                StreamRecord(stream_id="S-401", description="To storage", source_unit_id="PU-201", destination_unit_id="TK-301", stream_role="product", section_id="purification", temperature_c=60.0, pressure_bar=1.8, components=[]),
                StreamRecord(stream_id="S-402", description="Dispatch", source_unit_id="TK-301", stream_role="product", section_id="storage", temperature_c=32.0, pressure_bar=1.1, components=[]),
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        semantics = build_pid_lite_semantics(flowsheet_graph, stream_table, control_plan, library, target)

        unit_ids = {entity.unit_id for entity in semantics.entities if entity.diagram_level == DiagramLevel.PID_LITE and entity.kind == DiagramEntityKind.UNIT}
        relief_anchors = {entity.attached_to_entity_id for entity in semantics.entities if entity.symbol_key == "pid_relief_valve"}

        self.assertTrue({"R-101", "PU-201", "TK-301"}.issubset(unit_ids))
        self.assertTrue({"pid_unit_r_101", "pid_unit_pu_201", "pid_unit_tk_301"}.issubset(relief_anchors))

    def test_phase22_bac_pid_titles_and_line_classes_render_stably(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_render",
            route_id="route_bac_pid_render",
            operating_mode="continuous",
            nodes=[FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction")],
            unit_models=[],
            section_ids=["reaction"],
            stream_ids=["S-201"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=3.1,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    stream_role="intermediate",
                    section_id="reaction",
                )
            ],
            closure_error_pct=0.5,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, target=target)
        signature = self._pid_svg_regression_signature(artifact)
        expected = self._fixture_path("bac_pid_reaction_signature.txt").read_text()
        self.assertEqual(signature, expected)

    def test_phase22_bac_pid_multi_sheet_titles_and_relief_callouts_render_stably(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_multisheet",
            route_id="route_bac_pid_multisheet",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="PU-201", unit_type="distillation_column", label="Purification Column", section_id="purification"),
                FlowsheetNode(node_id="TK-301", unit_type="tank", label="Product Storage Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification", "storage"],
            stream_ids=["S-201", "S-401", "S-402"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=2.8,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    destination_unit_id="PU-201",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S-401",
                    description="To storage",
                    temperature_c=60.0,
                    pressure_bar=1.8,
                    components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)],
                    source_unit_id="PU-201",
                    destination_unit_id="TK-301",
                    stream_role="product",
                    section_id="purification",
                ),
                StreamRecord(
                    stream_id="S-402",
                    description="Dispatch",
                    temperature_c=32.0,
                    pressure_bar=1.1,
                    components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)],
                    source_unit_id="TK-301",
                    stream_role="product",
                    section_id="storage",
                ),
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, target=target)
        signature = self._pid_multi_sheet_signature(artifact)
        expected = self._fixture_path("bac_pid_multisheet_signature.txt").read_text()
        self.assertEqual(signature, expected)

    def test_phase23_bac_pfd_sheet_composition_uses_stitched_panel_metadata(self):
        artifact = self._build_bac_pfd_regression_artifact()
        self.assertEqual(
            [sheet.title for sheet in artifact.sheets],
            [
                "BAC PFD Panel 1: Feed, Reaction, and Cleanup",
                "BAC PFD Panel 2: Purification, Storage, and Offsites",
            ],
        )
        self.assertEqual(artifact.sheets[0].stitch_panel_id, "bac-pfd-panel-1")
        self.assertEqual(artifact.sheets[0].stitch_next_sheet_id, "sheet_2")
        self.assertEqual(artifact.sheets[1].stitch_prev_sheet_id, "sheet_1")
        self.assertIn("Panel 2: Purification,", artifact.sheets[0].svg)

    def test_phase23_bac_pid_sheets_include_stitched_panel_metadata_and_markers(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        style = build_diagram_style_profile()
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_phase23",
            route_id="route_bac_pid_phase23",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="PU-201", unit_type="distillation_column", label="Purification Column", section_id="purification"),
                FlowsheetNode(node_id="TK-301", unit_type="tank", label="Product Storage Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification", "storage"],
            stream_ids=["S-201", "S-401", "S-402"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(
                    stream_id="S-201",
                    description="Reactor effluent",
                    temperature_c=85.0,
                    pressure_bar=2.8,
                    components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)],
                    source_unit_id="R-101",
                    destination_unit_id="PU-201",
                    stream_role="intermediate",
                    section_id="reaction",
                ),
                StreamRecord(
                    stream_id="S-401",
                    description="To storage",
                    temperature_c=60.0,
                    pressure_bar=1.8,
                    components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)],
                    source_unit_id="PU-201",
                    destination_unit_id="TK-301",
                    stream_role="product",
                    section_id="purification",
                ),
                StreamRecord(
                    stream_id="S-402",
                    description="Dispatch",
                    temperature_c=32.0,
                    pressure_bar=1.1,
                    components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)],
                    source_unit_id="TK-301",
                    stream_role="product",
                    section_id="storage",
                ),
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, target=target)
        self.assertEqual(artifact.sheets[0].stitch_panel_id, "bac-pid-panel-1")
        self.assertEqual(artifact.sheets[1].stitch_prev_sheet_id, "sheet_1")
        self.assertEqual(artifact.sheets[1].stitch_next_sheet_id, "sheet_3")
        self.assertIn("Panel 2: BAC Reaction", artifact.sheets[0].svg)

    def test_phase24_bac_drawio_export_preserves_layers_and_stitch_metadata(self):
        artifact = self._build_bac_pfd_regression_artifact()
        library = build_diagram_symbol_library()
        style = build_diagram_style_profile()
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pfd_fixture",
            route_id="route_bac_pfd_fixture",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed Preparation", section_id="feed"),
                FlowsheetNode(node_id="reactor", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="primary_flash", unit_type="flash_vessel", label="Primary Flash", section_id="cleanup"),
                FlowsheetNode(node_id="concentration", unit_type="heat_exchanger", label="Concentration", section_id="concentration"),
                FlowsheetNode(node_id="purification", unit_type="distillation_column", label="Purification", section_id="purification"),
                FlowsheetNode(node_id="storage", unit_type="tank", label="Storage", section_id="storage"),
                FlowsheetNode(node_id="waste_treatment", unit_type="waste_treatment", label="Waste Treatment", section_id="waste_treatment"),
            ],
            unit_models=[],
            section_ids=["feed", "reaction", "cleanup", "concentration", "purification", "storage", "waste_treatment"],
            stream_ids=["S-101", "S-102", "S-150", "S-201", "S-202", "S-203", "S-401", "S-402", "S-403", "S-404"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(stream_id="S-101", description="Fresh BAC feed", temperature_c=25.0, pressure_bar=1.0, components=[], destination_unit_id="feed_prep", stream_role="feed", section_id="feed"),
                StreamRecord(stream_id="S-102", description="Diluent feed", temperature_c=25.0, pressure_bar=1.0, components=[], destination_unit_id="feed_prep", stream_role="feed", section_id="feed"),
                StreamRecord(stream_id="S-150", description="Reactor feed", temperature_c=45.0, pressure_bar=2.0, components=[], source_unit_id="feed_prep", destination_unit_id="reactor", stream_role="intermediate", section_id="reaction"),
                StreamRecord(stream_id="S-201", description="Reactor effluent", temperature_c=85.0, pressure_bar=3.1, components=[], source_unit_id="reactor", destination_unit_id="primary_flash", stream_role="intermediate", section_id="cleanup"),
                StreamRecord(stream_id="S-202", description="Vent purge", temperature_c=55.0, pressure_bar=1.2, components=[], source_unit_id="primary_flash", destination_unit_id="waste_treatment", stream_role="vent", section_id="cleanup"),
                StreamRecord(stream_id="S-203", description="Rich liquid to cleanup", temperature_c=70.0, pressure_bar=2.4, components=[], source_unit_id="primary_flash", destination_unit_id="concentration", stream_role="intermediate", section_id="cleanup"),
                StreamRecord(stream_id="S-401", description="Recycle return", temperature_c=40.0, pressure_bar=1.4, components=[], source_unit_id="purification", stream_role="recycle", section_id="purification"),
                StreamRecord(stream_id="S-402", description="Product to storage", temperature_c=35.0, pressure_bar=1.1, components=[], source_unit_id="purification", destination_unit_id="storage", stream_role="product", section_id="purification"),
                StreamRecord(stream_id="S-403", description="Waste to ETP", temperature_c=32.0, pressure_bar=1.0, components=[], source_unit_id="storage", destination_unit_id="waste_treatment", stream_role="waste", section_id="storage"),
                StreamRecord(stream_id="S-404", description="Side draw", temperature_c=48.0, pressure_bar=1.3, components=[], source_unit_id="purification", destination_unit_id="waste_treatment", stream_role="side_draw", section_id="purification"),
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_case = FlowsheetCase(
            case_id="case_bac_pfd_fixture",
            route_id="route_bac_pfd_fixture",
            operating_mode="continuous",
            units=[],
            streams=[
                StreamSpec(stream_id="S-101", destination_unit_id="feed_prep", stream_role="feed", section_id="feed"),
                StreamSpec(stream_id="S-102", destination_unit_id="feed_prep", stream_role="feed", section_id="feed"),
                StreamSpec(stream_id="S-150", source_unit_id="feed_prep", destination_unit_id="reactor", stream_role="intermediate", section_id="reaction"),
                StreamSpec(stream_id="S-201", source_unit_id="reactor", destination_unit_id="primary_flash", stream_role="intermediate", section_id="cleanup"),
                StreamSpec(stream_id="S-202", source_unit_id="primary_flash", destination_unit_id="waste_treatment", stream_role="vent", section_id="cleanup"),
                StreamSpec(stream_id="S-203", source_unit_id="primary_flash", destination_unit_id="concentration", stream_role="intermediate", section_id="cleanup"),
                StreamSpec(stream_id="S-401", source_unit_id="purification", stream_role="recycle", section_id="purification"),
                StreamSpec(stream_id="S-402", source_unit_id="purification", destination_unit_id="storage", stream_role="product", section_id="purification"),
                StreamSpec(stream_id="S-403", source_unit_id="storage", destination_unit_id="waste_treatment", stream_role="waste", section_id="storage"),
                StreamSpec(stream_id="S-404", source_unit_id="purification", destination_unit_id="waste_treatment", stream_role="side_draw", section_id="purification"),
            ],
            composition_states=[],
            composition_closures=[],
            separations=[],
            recycle_loops=[],
            convergence_summaries=[],
            unit_operation_packets=[],
            sections=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        semantics = build_process_flow_diagram_semantics(flowsheet_graph, flowsheet_case, stream_table, target, library)
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        drawio = build_drawio_document(
            diagram_id=artifact.diagram_id,
            title="BAC PFD",
            sheets=artifact.sheets,
            nodes=artifact.nodes,
            edges=artifact.edges,
            modules=modules,
            sheet_composition=composition,
        )
        expected = self._fixture_path("bac_drawio_signature.txt").read_text()
        actual = self._bac_drawio_signature(drawio)
        self.assertEqual(actual, expected)

    def test_phase25_bac_diagram_benchmark_artifact_passes_for_locked_package(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        style = build_diagram_style_profile()
        library = build_diagram_symbol_library()
        blueprint = FlowsheetBlueprintArtifact(
            blueprint_id="bp_bac_benchmark_bfd",
            route_id="bac_benchmark_bfd",
            route_name="BAC Benchmark Route",
            route_family="quaternary_ammonium",
            steps=[
                FlowsheetBlueprintStep(step_id="step_feed", route_id="bac_benchmark_bfd", section_id="feed preparation", section_label="feed prep", step_role="feed", unit_id="feed_prep", unit_type="mixing", service="feed prep", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_reaction", route_id="bac_benchmark_bfd", section_id="reaction", section_label="quaternization", step_role="reaction", unit_id="reactor", unit_type="cstr", service="reaction", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_cleanup", route_id="bac_benchmark_bfd", section_id="cleanup", section_label="cleanup", step_role="cleanup", unit_id="flash", unit_type="flash_vessel", service="cleanup", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_concentration", route_id="bac_benchmark_bfd", section_id="concentration", section_label="concentration", step_role="concentration", unit_id="concentrator", unit_type="heat_exchanger", service="concentration", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_purification", route_id="bac_benchmark_bfd", section_id="purification", section_label="purification", step_role="purification", unit_id="column", unit_type="distillation_column", service="purification", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_storage", route_id="bac_benchmark_bfd", section_id="storage", section_label="product tankage", step_role="storage", unit_id="tank_farm", unit_type="storage_tank", service="storage", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_waste", route_id="bac_benchmark_bfd", section_id="waste handling", section_label="waste handling", step_role="waste handling", unit_id="waste_receiver", unit_type="waste_treatment", service="waste handling", citations=["s1"], assumptions=["seed"]),
            ],
            recycle_intents=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        bfd = build_block_flow_diagram(blueprint, style, target)
        pfd = self._build_bac_pfd_regression_artifact()
        pfd_acceptance = DiagramAcceptanceArtifact(
            diagram_id="bac_benchmark_pfd_acceptance",
            diagram_kind="pfd",
            overall_status="complete",
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        flowsheet_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_multisheet",
            route_id="route_bac_pid_multisheet",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="PU-201", unit_type="distillation_column", label="Purification Column", section_id="purification"),
                FlowsheetNode(node_id="TK-301", unit_type="tank", label="Product Storage Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification", "storage"],
            stream_ids=["S-201", "S-401", "S-402"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        stream_table = StreamTable(
            streams=[
                StreamRecord(stream_id="S-201", description="Reactor effluent", temperature_c=85.0, pressure_bar=2.8, components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)], source_unit_id="R-101", destination_unit_id="PU-201", stream_role="intermediate", section_id="reaction"),
                StreamRecord(stream_id="S-401", description="To storage", temperature_c=60.0, pressure_bar=1.8, components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)], source_unit_id="PU-201", destination_unit_id="TK-301", stream_role="product", section_id="purification"),
                StreamRecord(stream_id="S-402", description="Dispatch", temperature_c=32.0, pressure_bar=1.1, components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)], source_unit_id="TK-301", stream_role="product", section_id="storage"),
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        pid = build_pid_lite_diagram(flowsheet_graph, stream_table, control_plan, style, target=target)
        semantics = build_process_flow_diagram_semantics(
            FlowsheetGraph(
                graph_id="fg_bac_pfd_fixture",
                route_id="route_bac_pfd_fixture",
                operating_mode="continuous",
                nodes=[
                    FlowsheetNode(node_id="feed_prep", unit_type="feed_preparation", label="Feed Preparation", section_id="feed"),
                    FlowsheetNode(node_id="reactor", unit_type="cstr", label="Reactor", section_id="reaction"),
                    FlowsheetNode(node_id="primary_flash", unit_type="flash_vessel", label="Primary Flash", section_id="cleanup"),
                    FlowsheetNode(node_id="concentration", unit_type="heat_exchanger", label="Concentration", section_id="concentration"),
                    FlowsheetNode(node_id="purification", unit_type="distillation_column", label="Purification", section_id="purification"),
                    FlowsheetNode(node_id="storage", unit_type="tank", label="Storage", section_id="storage"),
                    FlowsheetNode(node_id="waste_treatment", unit_type="waste_treatment", label="Waste Treatment", section_id="waste_treatment"),
                ],
                unit_models=[],
                section_ids=["feed", "reaction", "cleanup", "concentration", "purification", "storage", "waste_treatment"],
                stream_ids=["S-101", "S-102", "S-150", "S-201", "S-202", "S-203", "S-401", "S-402", "S-403", "S-404"],
                markdown="seed",
                citations=["s1"],
                assumptions=["seed"],
            ),
            FlowsheetCase(case_id="case_bac_pfd_fixture", route_id="route_bac_pfd_fixture", operating_mode="continuous", units=[], streams=[], composition_states=[], composition_closures=[], separations=[], recycle_loops=[], convergence_summaries=[], unit_operation_packets=[], sections=[], markdown="seed", citations=["s1"], assumptions=["seed"]),
            StreamTable(streams=[], closure_error_pct=0.0, markdown="seed", citations=["s1"], assumptions=["seed"]),
            target,
            library,
        )
        modules = build_process_flow_diagram_modules(semantics, library)
        composition = build_process_flow_diagram_sheet_composition(modules, semantics, style, target)
        drawio = build_drawio_document(
            diagram_id=pfd.diagram_id,
            title="BAC PFD",
            sheets=pfd.sheets,
            nodes=pfd.nodes,
            edges=pfd.edges,
            modules=modules,
            sheet_composition=composition,
        )
        artifact = build_bac_diagram_benchmark_artifact(
            route_id="bac_benchmark_suite",
            target=target,
            bfd=bfd,
            pfd=pfd,
            pfd_acceptance=pfd_acceptance,
            pid=pid,
            drawio_document=drawio,
        )

        self.assertEqual(artifact.overall_status, "complete")
        self.assertEqual([row.diagram_kind for row in artifact.rows], ["bfd", "pfd", "pid", "drawio"])
        self.assertTrue(all(row.status == "pass" for row in artifact.rows))

    def test_phase26_bac_drawing_package_artifact_builds_register_and_paths(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        bfd_sheets = [DiagramSheet(sheet_id="sheet_1", title="Block Flow Diagram")]
        pfd_sheets = [
            DiagramSheet(sheet_id="sheet_1", title="BAC PFD Panel 1: Feed, Reaction, and Cleanup"),
            DiagramSheet(sheet_id="sheet_2", title="BAC PFD Panel 2: Purification, Storage, and Offsites"),
        ]
        pid_sheets = [
            DiagramSheet(sheet_id="sheet_1", title="BAC Reaction P&ID: Reactor"),
            DiagramSheet(sheet_id="sheet_2", title="BAC Purification P&ID: Purification Column"),
            DiagramSheet(sheet_id="sheet_3", title="BAC Storage P&ID: Product Storage"),
        ]
        apply_diagram_drafting_metadata(bfd_sheets, drawing_prefix="bac-bfd")
        apply_diagram_drafting_metadata(pfd_sheets, drawing_prefix="bac-pfd")
        apply_diagram_drafting_metadata(pid_sheets, drawing_prefix="bac-pid")
        bfd = BlockFlowDiagramArtifact(diagram_id="bac_bfd", route_id="bac_route", sheets=bfd_sheets, markdown="seed", citations=["s1"], assumptions=["seed"])
        pfd = ProcessFlowDiagramArtifact(diagram_id="bac_pfd", route_id="bac_route", sheets=pfd_sheets, markdown="seed", citations=["s1"], assumptions=["seed"])
        pid = PidLiteDiagramArtifact(diagram_id="bac_pid", route_id="bac_route", sheets=pid_sheets, markdown="seed", citations=["s1"], assumptions=["seed"])
        benchmark = BACDiagramBenchmarkArtifact(
            artifact_id="bac_benchmark",
            route_id="bac_route",
            overall_status="complete",
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_bac_drawing_package_artifact(
            route_id="bac_route",
            target=target,
            bfd=bfd,
            pfd=pfd,
            pid=pid,
            benchmark=benchmark,
            base_output_dir="outputs/bac/diagrams",
        )

        self.assertEqual(artifact.overall_status, "complete")
        self.assertEqual(artifact.benchmark_status, "complete")
        self.assertEqual(len(artifact.register_rows), 6)
        self.assertIn("outputs/bac/diagrams/bfd_sheet_1.svg", artifact.svg_paths)
        self.assertIn("outputs/bac/diagrams/pfd.drawio", artifact.drawio_paths)
        self.assertIn("BAC PFD Panel 2: Purification, Storage, and Offsites", artifact.markdown)

    def test_phase27_bac_drawing_package_tracks_review_workflow(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        bfd_sheets = [DiagramSheet(sheet_id="sheet_1", title="Block Flow Diagram", issue_status="For Review")]
        pfd_sheets = [
            DiagramSheet(sheet_id="sheet_1", title="BAC PFD Panel 1: Feed, Reaction, and Cleanup", issue_status="Approved"),
            DiagramSheet(sheet_id="sheet_2", title="BAC PFD Panel 2: Purification, Storage, and Offsites", issue_status="Approved"),
        ]
        pid_sheets = [
            DiagramSheet(sheet_id="sheet_1", title="BAC Reaction P&ID: Reactor", issue_status="Approved"),
            DiagramSheet(sheet_id="sheet_2", title="BAC Purification P&ID: Purification Column", issue_status="Approved"),
            DiagramSheet(sheet_id="sheet_3", title="BAC Storage P&ID: Product Storage", issue_status="Approved"),
        ]
        apply_diagram_drafting_metadata(bfd_sheets, drawing_prefix="bac-bfd")
        apply_diagram_drafting_metadata(pfd_sheets, drawing_prefix="bac-pfd")
        apply_diagram_drafting_metadata(pid_sheets, drawing_prefix="bac-pid")
        apply_diagram_review_workflow_metadata(
            pfd_sheets + pid_sheets,
            checked_by="CHK-1",
            reviewed_by="RVW-1",
            approved_by="APR-1",
            approved_date="2026-04-13",
        )
        apply_diagram_review_workflow_metadata(
            bfd_sheets,
            checked_by="CHK-1",
            reviewed_by="RVW-1",
        )
        bfd = BlockFlowDiagramArtifact(diagram_id="bac_bfd", route_id="bac_route", sheets=bfd_sheets, markdown="seed", citations=["s1"], assumptions=["seed"])
        pfd = ProcessFlowDiagramArtifact(diagram_id="bac_pfd", route_id="bac_route", sheets=pfd_sheets, markdown="seed", citations=["s1"], assumptions=["seed"])
        pid = PidLiteDiagramArtifact(diagram_id="bac_pid", route_id="bac_route", sheets=pid_sheets, markdown="seed", citations=["s1"], assumptions=["seed"])
        benchmark = BACDiagramBenchmarkArtifact(
            artifact_id="bac_benchmark",
            route_id="bac_route",
            overall_status="complete",
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )

        artifact = build_bac_drawing_package_artifact(
            route_id="bac_route",
            target=target,
            bfd=bfd,
            pfd=pfd,
            pid=pid,
            benchmark=benchmark,
            base_output_dir="outputs/bac/diagrams",
        )

        self.assertEqual(artifact.review_workflow_status, "for_review")
        self.assertEqual(artifact.checker, "CHK-1")
        self.assertEqual(artifact.reviewer, "RVW-1")
        self.assertEqual(artifact.approver, "APR-1")
        self.assertIn("A:Approved", artifact.revision_history)

    def test_bac_rendering_audit_artifact_reports_current_locked_package_as_complete(self):
        target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        style = build_diagram_style_profile()
        blueprint = FlowsheetBlueprintArtifact(
            blueprint_id="bp_bac_render_audit",
            route_id="bac_render_audit_bfd",
            route_name="BAC Render Audit",
            route_family="quaternary_ammonium",
            steps=[
                FlowsheetBlueprintStep(step_id="step_feed", route_id="bac_render_audit_bfd", section_id="feed preparation", section_label="feed prep", step_role="feed", unit_id="feed_prep", unit_type="mixing", service="feed prep", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_reaction", route_id="bac_render_audit_bfd", section_id="reaction", section_label="quaternization", step_role="reaction", unit_id="reactor", unit_type="cstr", service="reaction", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_cleanup", route_id="bac_render_audit_bfd", section_id="cleanup", section_label="cleanup", step_role="cleanup", unit_id="flash", unit_type="flash_vessel", service="cleanup", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_concentration", route_id="bac_render_audit_bfd", section_id="concentration", section_label="concentration", step_role="concentration", unit_id="concentrator", unit_type="heat_exchanger", service="concentration", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_purification", route_id="bac_render_audit_bfd", section_id="purification", section_label="purification", step_role="purification", unit_id="column", unit_type="distillation_column", service="purification", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_storage", route_id="bac_render_audit_bfd", section_id="storage", section_label="product tankage", step_role="storage", unit_id="tank_farm", unit_type="storage_tank", service="storage", citations=["s1"], assumptions=["seed"]),
                FlowsheetBlueprintStep(step_id="step_waste", route_id="bac_render_audit_bfd", section_id="waste handling", section_label="waste handling", step_role="waste handling", unit_id="waste_receiver", unit_type="waste_treatment", service="waste handling", citations=["s1"], assumptions=["seed"]),
            ],
            recycle_intents=[],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        bfd = build_block_flow_diagram(blueprint, style, target)
        pfd = self._build_bac_pfd_regression_artifact()
        pfd_acceptance = DiagramAcceptanceArtifact(
            diagram_id="bac_render_audit_pfd_acceptance",
            diagram_kind="pfd",
            overall_status="complete",
            benchmark_cleanliness_score=0.91,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        pfd_routing = DiagramRoutingArtifact(
            diagram_id="bac_render_audit_pfd_routing",
            route_id="bac_render_audit",
            diagram_level=DiagramLevel.PFD,
            sheets=[
                DiagramRoutingSheet(sheet_id="sheet_1", continuation_markers=[], crossing_count=0, congested_connector_count=0, max_channel_load=2),
                DiagramRoutingSheet(sheet_id="sheet_2", continuation_markers=[], crossing_count=0, congested_connector_count=0, max_channel_load=2),
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        pid_target = build_diagram_target_profile(ProjectBasis(target_product="Benzalkonium chloride", capacity_tpa=1000, target_purity_wt_pct=99.0))
        pid_graph = FlowsheetGraph(
            graph_id="fg_bac_pid_multisheet",
            route_id="route_bac_pid_multisheet",
            operating_mode="continuous",
            nodes=[
                FlowsheetNode(node_id="R-101", unit_type="cstr", label="Reactor", section_id="reaction"),
                FlowsheetNode(node_id="PU-201", unit_type="distillation_column", label="Purification Column", section_id="purification"),
                FlowsheetNode(node_id="TK-301", unit_type="tank", label="Product Storage Tank", section_id="storage"),
            ],
            unit_models=[],
            section_ids=["reaction", "purification", "storage"],
            stream_ids=["S-201", "S-401", "S-402"],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        pid_streams = StreamTable(
            streams=[
                StreamRecord(stream_id="S-201", description="Reactor effluent", temperature_c=85.0, pressure_bar=2.8, components=[StreamComponentFlow(name="B", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.1)], source_unit_id="R-101", destination_unit_id="PU-201", stream_role="intermediate", section_id="reaction"),
                StreamRecord(stream_id="S-401", description="To storage", temperature_c=60.0, pressure_bar=1.8, components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)], source_unit_id="PU-201", destination_unit_id="TK-301", stream_role="product", section_id="purification"),
                StreamRecord(stream_id="S-402", description="Dispatch", temperature_c=32.0, pressure_bar=1.1, components=[StreamComponentFlow(name="BAC", mass_flow_kg_hr=8.0, molar_flow_kmol_hr=0.02)], source_unit_id="TK-301", stream_role="product", section_id="storage"),
            ],
            closure_error_pct=0.0,
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        control_plan = ControlPlanArtifact(
            control_loops=[
                ControlLoop(
                    control_id="PIC-101",
                    unit_id="R-101",
                    loop_family="pressure",
                    controlled_variable="Reactor pressure",
                    manipulated_variable="Vent valve",
                    sensor="PT-101",
                    actuator="PV-101",
                    objective="Maintain reactor pressure",
                    startup_logic="seed",
                    shutdown_logic="seed",
                    override_logic="seed",
                    safeguard_linkage="Reactor overpressure relief",
                    criticality="high",
                    notes="seed",
                    citations=["s1"],
                    assumptions=["seed"],
                )
            ],
            markdown="seed",
            citations=["s1"],
            assumptions=["seed"],
        )
        pid = build_pid_lite_diagram(pid_graph, pid_streams, control_plan, style, target=pid_target)

        artifact = build_bac_rendering_audit_artifact(
            route_id="bac_render_audit",
            target=target,
            bfd=bfd,
            pfd=pfd,
            pfd_acceptance=pfd_acceptance,
            pfd_routing=pfd_routing,
            pid=pid,
        )

        self.assertEqual(artifact.overall_status, "complete")
        self.assertEqual([row.diagram_kind for row in artifact.rows], ["bfd", "pfd", "pid"])
        self.assertTrue(all(row.status == "pass" for row in artifact.rows))


if __name__ == "__main__":
    unittest.main()
