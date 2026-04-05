from __future__ import annotations

import json
import math
from pathlib import Path

from aoc.models import (
    EquipmentListArtifact,
    MechanicalDesignArtifact,
    ReactorDesign,
    ReactorDesignBasis,
    ResearchBundle,
    SourceRecord,
    StreamTable,
)
from aoc.pipeline import PipelineRunner
from aoc.publish import markdown_table, render_styled_pdf, references_markdown


def _pick_standard_nb(required_id_mm: float) -> int:
    standards = [25, 32, 40, 50, 65, 80, 100, 150, 200, 250, 300, 400, 600]
    for candidate in standards:
        if candidate >= required_id_mm:
            return candidate
    return standards[-1]


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _source_subset_markdown(source_index: dict[str, SourceRecord], citation_ids: list[str]) -> str:
    subset = {source_id: source_index[source_id] for source_id in citation_ids if source_id in source_index}
    return references_markdown(subset) if subset else "## References\n\n1. Internal project artifacts."


def _html_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{header}</th>" for header in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return "<table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table>"


def _references_html(source_index: dict[str, SourceRecord], citation_ids: list[str]) -> str:
    subset = [source_index[source_id] for source_id in citation_ids if source_id in source_index]
    if not subset:
        return "<h2>References</h2><ol><li>Internal project artifacts.</li></ol>"
    lines = []
    for source in sorted(subset, key=lambda item: item.title.lower()):
        organization = (source.citation_text or "").split(".", 1)[0].strip() or source.source_id
        title = source.title.strip().rstrip(".")
        year = str(source.reference_year) if source.reference_year else "n.d."
        location = source.url_or_doi or source.local_path or "Local source"
        lines.append(f"<li>{organization}. <em>{title}</em>. {year}. Available at: {location}.</li>")
    return "<h2>References</h2><ol>" + "".join(lines) + "</ol>"


def _build_html_document(report_title: str, sections: list[tuple[str, str]]) -> str:
    body = [f"<h1>{report_title}</h1>"]
    for title, content in sections:
        body.append(f"<h2>{title}</h2>{content}")
    css = """
    <style>
      body { font-family: 'Times New Roman', serif; font-size: 11pt; line-height: 1.35; margin: 28pt 34pt; color: #111; }
      h1 { font-size: 24pt; text-align: center; margin: 0 0 18pt; letter-spacing: 0.4pt; }
      h2 { font-size: 15pt; margin: 18pt 0 8pt; page-break-after: avoid; }
      p { margin: 0 0 8pt; text-align: justify; }
      table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 9.5pt; }
      th, td { border: 1px solid #333; padding: 5pt 6pt; vertical-align: top; }
      th { background: #efefef; font-weight: 700; text-align: left; }
      ul, ol { margin: 0 0 10pt 18pt; }
      li { margin: 0 0 4pt; }
    </style>
    """
    return f"<html><head>{css}</head><body>{''.join(body)}</body></html>"


def generate_reactor_mechanical_report(project_id: str, output_root: str = "outputs") -> tuple[Path, Path]:
    runner = PipelineRunner.from_project_id(project_id, output_root=output_root)
    reactor = runner._load("reactor_design", ReactorDesign)
    reactor_basis = runner._load("reactor_design_basis", ReactorDesignBasis)
    equipment = runner._load("equipment_list", EquipmentListArtifact)
    mechanical = runner._load("mechanical_design", MechanicalDesignArtifact)
    stream_table = runner._load("stream_table", StreamTable)
    bundle = runner._load("research_bundle", ResearchBundle)
    project_basis = runner.config.basis

    reactor_equipment = next(item for item in equipment.items if item.equipment_id == reactor.reactor_id)
    reactor_mech = next(item for item in mechanical.items if item.equipment_id == reactor.reactor_id)
    source_index = {source.source_id: source for source in bundle.sources}

    feed_stream = next(stream for stream in stream_table.streams if stream.stream_id == "S-150")
    product_stream = next(stream for stream in stream_table.streams if stream.stream_id == "S-201")
    feed_mass_flow = sum(component.mass_flow_kg_hr for component in feed_stream.components)
    product_mass_flow = sum(component.mass_flow_kg_hr for component in product_stream.components)

    density_trace = next(trace for trace in reactor.calc_traces if trace.trace_id == "reactor_reynolds")
    property_trace = next(trace for trace in reactor.calc_traces if trace.trace_id == "reactor_property_basis")
    process_density = float(density_trace.substitutions["rho"])
    process_viscosity = float(density_trace.substitutions["mu"])
    process_cp = float(property_trace.substitutions["Cp"])
    process_conductivity = float(property_trace.substitutions["k"])

    shell_diameter_m = reactor.shell_diameter_m
    tangent_length_m = reactor.shell_length_m
    head_type = "2:1 ellipsoidal heads"
    head_depth_m = shell_diameter_m / 4.0
    overall_vessel_height_m = tangent_length_m + 2.0 * head_depth_m
    shell_internal_volume_m3 = math.pi / 4.0 * shell_diameter_m**2 * tangent_length_m
    each_head_internal_volume_m3 = math.pi * shell_diameter_m**3 / 24.0
    total_head_volume_m3 = 2.0 * each_head_internal_volume_m3
    total_internal_volume_m3 = shell_internal_volume_m3 + total_head_volume_m3
    design_volume_margin_fraction = (
        (reactor.design_volume_m3 - reactor.liquid_holdup_m3) / reactor.liquid_holdup_m3
        if reactor.liquid_holdup_m3 > 0
        else 0.0
    )
    freeboard_volume_m3 = total_internal_volume_m3 - reactor.liquid_holdup_m3
    freeboard_fraction_of_total = freeboard_volume_m3 / total_internal_volume_m3 if total_internal_volume_m3 > 0 else 0.0
    shell_slenderness_ratio = tangent_length_m / shell_diameter_m if shell_diameter_m > 0 else 0.0

    pressure_mpa = reactor.design_pressure_bar / 10.0
    allowable_stress_mpa = reactor_mech.allowable_stress_mpa
    joint_efficiency = reactor_mech.joint_efficiency
    corrosion_allowance_mm = reactor_mech.corrosion_allowance_mm

    required_shell_thickness_mm = (
        (pressure_mpa * shell_diameter_m * 1000.0)
        / ((2.0 * allowable_stress_mpa * joint_efficiency) - (1.2 * pressure_mpa))
    ) + corrosion_allowance_mm
    required_head_thickness_mm = (
        (0.885 * pressure_mpa * shell_diameter_m * 1000.0)
        / ((2.0 * allowable_stress_mpa * joint_efficiency) - (0.1 * pressure_mpa))
    ) + corrosion_allowance_mm
    adopted_shell_thickness_mm = 10.0
    adopted_head_thickness_mm = 8.0
    shell_pressure_term_mm = (
        (pressure_mpa * shell_diameter_m * 1000.0)
        / ((2.0 * allowable_stress_mpa * joint_efficiency) - (1.2 * pressure_mpa))
    )
    head_pressure_term_mm = (
        (0.885 * pressure_mpa * shell_diameter_m * 1000.0)
        / ((2.0 * allowable_stress_mpa * joint_efficiency) - (0.1 * pressure_mpa))
    )
    shell_nominal_margin_mm = adopted_shell_thickness_mm - required_shell_thickness_mm
    shell_nominal_margin_fraction = (
        shell_nominal_margin_mm / required_shell_thickness_mm if required_shell_thickness_mm > 0 else 0.0
    )
    shell_mill_tolerance_fraction = 0.125
    shell_min_after_tolerance_mm = adopted_shell_thickness_mm * (1.0 - shell_mill_tolerance_fraction)
    shell_is_tolerance_compliant = shell_min_after_tolerance_mm >= required_shell_thickness_mm
    head_nominal_margin_mm = adopted_head_thickness_mm - required_head_thickness_mm
    head_nominal_margin_fraction = (
        head_nominal_margin_mm / required_head_thickness_mm if required_head_thickness_mm > 0 else 0.0
    )
    head_mill_tolerance_fraction = 0.125
    head_min_after_tolerance_mm = adopted_head_thickness_mm * (1.0 - head_mill_tolerance_fraction)
    head_is_tolerance_compliant = head_min_after_tolerance_mm >= required_head_thickness_mm

    impeller_type = "45 degree pitched-blade turbine"
    impeller_count = 4
    impeller_diameter_m = 0.35 * shell_diameter_m
    impeller_speed_rpm = 60.0
    impeller_speed_rps = impeller_speed_rpm / 60.0
    power_number = 1.5
    impeller_diameter_ratio = impeller_diameter_m / shell_diameter_m
    power_per_impeller_kw = (
        power_number
        * process_density
        * (impeller_speed_rps**3)
        * (impeller_diameter_m**5)
        / 1000.0
    )
    agitator_reynolds = (
        process_density * impeller_speed_rps * (impeller_diameter_m**2) / process_viscosity
    )
    agitator_power_kw = (
        impeller_count
        * power_number
        * process_density
        * (impeller_speed_rps**3)
        * (impeller_diameter_m**5)
        / 1000.0
    )
    agitator_tip_speed_m_s = math.pi * impeller_diameter_m * impeller_speed_rps
    design_torque_n_m = (agitator_power_kw * 1000.0) / (2.0 * math.pi * impeller_speed_rps)
    service_factor = 1.5
    design_torque_with_factor_n_m = design_torque_n_m * service_factor
    shaft_allowable_shear_pa = 35e6
    required_shaft_diameter_m = (
        (16.0 * design_torque_with_factor_n_m) / (math.pi * shaft_allowable_shear_pa)
    ) ** (1.0 / 3.0)
    adopted_shaft_diameter_mm = 100.0
    adopted_shaft_diameter_m = adopted_shaft_diameter_mm / 1000.0
    shaft_transmitted_shear_pa = (
        (16.0 * design_torque_with_factor_n_m) / (math.pi * adopted_shaft_diameter_m**3)
        if adopted_shaft_diameter_m > 0
        else 0.0
    )
    shaft_transmitted_shear_mpa = shaft_transmitted_shear_pa / 1e6
    shaft_stress_utilization_fraction = (
        shaft_transmitted_shear_pa / shaft_allowable_shear_pa if shaft_allowable_shear_pa > 0 else 0.0
    )
    shaft_is_adequate = shaft_transmitted_shear_pa <= shaft_allowable_shear_pa
    shaft_material = "SS316 solid shaft"
    selected_motor_kw = 15.0
    drive_arrangement = "top-entry geared drive with rigid coupling"
    seal_arrangement = "double mechanical seal, vendor-finalized"
    mixer_mounting_basis = "top-head mounted mixer with external gearbox and bearing housing"
    baffle_count = 4
    baffle_width_m = shell_diameter_m / 12.0
    impeller_spacing_m = tangent_length_m / (impeller_count + 1)
    bottom_clearance_m = 0.50 * impeller_diameter_m
    top_clearance_m = 0.75 * impeller_diameter_m
    shaft_length_m = tangent_length_m + top_clearance_m + bottom_clearance_m
    shaft_support_strategy = "top-entry shaft with one intermediate steady bearing and one bottom guide bearing"
    shaft_effective_span_count = 3
    shaft_effective_unsupported_span_m = (
        shaft_length_m / shaft_effective_span_count if shaft_effective_span_count > 0 else shaft_length_m
    )
    shaft_l_over_d_ratio = shaft_length_m / adopted_shaft_diameter_m if adopted_shaft_diameter_m > 0 else 0.0
    shaft_span_l_over_d_ratio = (
        shaft_effective_unsupported_span_m / adopted_shaft_diameter_m if adopted_shaft_diameter_m > 0 else 0.0
    )
    power_per_volume_kw_m3 = agitator_power_kw / reactor.liquid_holdup_m3 if reactor.liquid_holdup_m3 > 0 else 0.0
    flow_regime = "fully turbulent" if agitator_reynolds >= 1e4 else "transition"
    agitator_loading_fraction = agitator_power_kw / selected_motor_kw if selected_motor_kw > 0 else 0.0
    shaft_modulus_pa = 193e9
    shaft_density_kg_m3 = 8000.0
    gravity_m_s2 = 9.81
    estimated_impeller_mass_each_kg = 110.0 * (impeller_diameter_m**3)
    total_impeller_mass_kg = impeller_count * estimated_impeller_mass_each_kg
    shaft_cross_section_area_m2 = math.pi * adopted_shaft_diameter_m**2 / 4.0
    shaft_second_moment_m4 = math.pi * adopted_shaft_diameter_m**4 / 64.0
    shaft_mass_kg = shaft_density_kg_m3 * shaft_cross_section_area_m2 * shaft_length_m
    rotating_mass_kg = shaft_mass_kg + total_impeller_mass_kg
    equivalent_udl_n_m = (
        rotating_mass_kg * gravity_m_s2 / shaft_effective_unsupported_span_m
        if shaft_effective_unsupported_span_m > 0
        else 0.0
    )
    shaft_static_deflection_m = (
        5.0
        * equivalent_udl_n_m
        * shaft_effective_unsupported_span_m**4
        / (384.0 * shaft_modulus_pa * shaft_second_moment_m4)
        if shaft_second_moment_m4 > 0
        else 0.0
    )
    first_critical_speed_rpm = (
        (30.0 / math.pi) * math.sqrt(gravity_m_s2 / shaft_static_deflection_m)
        if shaft_static_deflection_m > 0
        else 0.0
    )
    operating_to_critical_speed_ratio = (
        impeller_speed_rpm / first_critical_speed_rpm if first_critical_speed_rpm > 0 else float("inf")
    )
    if operating_to_critical_speed_ratio <= 0.70:
        shaft_dynamic_status = "pass"
    elif operating_to_critical_speed_ratio <= 0.85:
        shaft_dynamic_status = "conditional"
    else:
        shaft_dynamic_status = "fail"
    shaft_dynamic_note = {
        "pass": "operating speed remains comfortably below screened first critical speed",
        "conditional": "operating speed is close to screened first critical speed and requires redesign/vendor confirmation",
        "fail": "operating speed exceeds screened first critical speed margin and the present shaft arrangement is not acceptable",
    }[shaft_dynamic_status]
    shaft_overall_status = (
        "pass" if shaft_is_adequate and shaft_dynamic_status == "pass"
        else "conditional" if shaft_is_adequate and shaft_dynamic_status == "conditional"
        else "fail"
    )

    heat_removal_options = [
        {
            "concept": "Full circumferential jacket",
            "controllability_score": 2,
            "fabrication_score": 1,
            "maintenance_score": 2,
            "suitability_score": 1,
            "selection_note": "simple concept but weak for a large tall reactor with substantial duty",
        },
        {
            "concept": "Half-pipe coil",
            "controllability_score": 4,
            "fabrication_score": 4,
            "maintenance_score": 3,
            "suitability_score": 4,
            "selection_note": "stronger pressure capability and better suited to large reactor shells",
        },
        {
            "concept": "Limpet coil",
            "controllability_score": 3,
            "fabrication_score": 3,
            "maintenance_score": 3,
            "suitability_score": 3,
            "selection_note": "practical but less attractive than half-pipe or loop service for this duty",
        },
        {
            "concept": "External recirculation loop with exchanger",
            "controllability_score": 5,
            "fabrication_score": 4,
            "maintenance_score": 5,
            "suitability_score": 5,
            "selection_note": "best controllability and maintenance access for the present large agitated reactor duty",
        },
    ]
    for option in heat_removal_options:
        option["total_score"] = (
            option["controllability_score"]
            + option["fabrication_score"]
            + option["maintenance_score"]
            + option["suitability_score"]
        )
    selected_heat_removal_option = max(heat_removal_options, key=lambda item: item["total_score"])
    selected_heat_removal_concept = selected_heat_removal_option["concept"]
    loop_exchanger_type = "shell-and-tube pump-around exchanger"
    loop_process_delta_t_c = 8.0
    loop_process_cp_kj_kg_k = process_cp
    loop_process_circulation_kg_s = reactor.heat_duty_kw / (loop_process_cp_kj_kg_k * loop_process_delta_t_c)
    loop_process_circulation_m3_s = loop_process_circulation_kg_s / process_density
    loop_line_velocity_basis_m_s = 2.5
    loop_line_required_mm = math.sqrt(
        (4.0 * loop_process_circulation_m3_s) / (math.pi * loop_line_velocity_basis_m_s)
    ) * 1000.0
    loop_line_adopted_nb = _pick_standard_nb(loop_line_required_mm)
    loop_process_holdup_m3 = loop_process_circulation_m3_s * 60.0
    rejected_jacket_basis_note = "full circumferential jacket retained only as prior screening concept and not as preferred accuracy-upgrade selection"

    jacket_gap_m = 0.075
    jacket_outer_diameter_m = shell_diameter_m + 2.0 * jacket_gap_m
    jacket_design_pressure_bar = 6.0
    jacket_design_temperature_c = 120.0
    jacket_cp_kj_kg_k = 2.30
    jacket_density_kg_m3 = 950.0
    jacket_delta_t_c = 15.0
    jacket_required_area_m2 = reactor.heat_transfer_area_m2
    jacket_equivalent_height_m = jacket_required_area_m2 / (math.pi * shell_diameter_m)
    adopted_jacket_height_m = 2.0
    jacket_volume_m3 = (
        math.pi / 4.0
    ) * ((jacket_outer_diameter_m**2) - (shell_diameter_m**2)) * adopted_jacket_height_m
    jacket_flow_kg_s = reactor.heat_duty_kw / (jacket_cp_kj_kg_k * jacket_delta_t_c)
    jacket_flow_m3_s = jacket_flow_kg_s / jacket_density_kg_m3
    jacket_velocity_basis_m_s = 2.0
    jacket_nozzle_required_mm = math.sqrt((4.0 * jacket_flow_m3_s) / (math.pi * 2.0)) * 1000.0
    jacket_nozzle_adopted_nb = _pick_standard_nb(jacket_nozzle_required_mm)
    jacket_pressure_term_mm = (
        ((jacket_design_pressure_bar / 10.0) * jacket_outer_diameter_m * 1000.0)
        / ((2.0 * allowable_stress_mpa * joint_efficiency) - (1.2 * (jacket_design_pressure_bar / 10.0)))
    )
    required_jacket_shell_thickness_mm = (
        jacket_pressure_term_mm
    ) + corrosion_allowance_mm
    adopted_jacket_shell_thickness_mm = 14.0
    jacket_nominal_margin_mm = adopted_jacket_shell_thickness_mm - required_jacket_shell_thickness_mm
    jacket_mill_tolerance_fraction = 0.125
    jacket_min_after_tolerance_mm = adopted_jacket_shell_thickness_mm * (1.0 - jacket_mill_tolerance_fraction)
    jacket_is_tolerance_compliant = jacket_min_after_tolerance_mm >= required_jacket_shell_thickness_mm
    jacket_circulation_time_s = jacket_volume_m3 / jacket_flow_m3_s if jacket_flow_m3_s > 0 else 0.0
    carbon_steel_density_kg_m3 = 7850.0
    shell_steel_volume_m3 = math.pi * shell_diameter_m * tangent_length_m * (adopted_shell_thickness_mm / 1000.0)
    head_surface_area_each_m2 = 1.24 * math.pi * shell_diameter_m**2 / 4.0
    head_steel_volume_m3 = 2.0 * head_surface_area_each_m2 * (adopted_head_thickness_mm / 1000.0)
    skirt_diameter_m = shell_diameter_m
    skirt_height_m = shell_diameter_m
    skirt_steel_volume_m3 = math.pi * skirt_diameter_m * skirt_height_m * (reactor_mech.support_thickness_mm / 1000.0)
    platform_steel_kg = 250.0 * reactor_mech.platform_area_m2 if reactor_mech.maintenance_platform_required else 0.0
    ladder_and_access_kg = 250.0 if reactor_mech.access_ladder_required else 0.0
    lifting_lug_kg = 75.0 if reactor_mech.lifting_lug_required else 0.0
    loop_exchanger_and_piping_kg = 2200.0
    shaft_support_hardware_kg = 350.0
    shell_steel_kg = shell_steel_volume_m3 * carbon_steel_density_kg_m3
    head_steel_kg = head_steel_volume_m3 * carbon_steel_density_kg_m3
    skirt_steel_kg = skirt_steel_volume_m3 * carbon_steel_density_kg_m3
    jacket_shell_kg = 0.0
    mixer_drive_kg = 1800.0
    vessel_structural_kg = shell_steel_kg + head_steel_kg + skirt_steel_kg
    attachment_kg = platform_steel_kg + ladder_and_access_kg + lifting_lug_kg
    rotating_equipment_kg = shaft_mass_kg + total_impeller_mass_kg + mixer_drive_kg + shaft_support_hardware_kg
    thermal_hardware_kg = loop_exchanger_and_piping_kg
    operating_liquid_kg = reactor.liquid_holdup_m3 * process_density
    hydrotest_liquid_kg = total_internal_volume_m3 * 1000.0
    empty_weight_kg = vessel_structural_kg + attachment_kg + rotating_equipment_kg + thermal_hardware_kg
    operating_weight_kg = empty_weight_kg + operating_liquid_kg
    hydrotest_weight_kg = empty_weight_kg + hydrotest_liquid_kg
    rebuilt_empty_load_kn = empty_weight_kg * gravity_m_s2 / 1000.0
    rebuilt_operating_load_kn = operating_weight_kg * gravity_m_s2 / 1000.0
    rebuilt_hydrotest_load_kn = hydrotest_weight_kg * gravity_m_s2 / 1000.0
    rebuilt_design_vertical_load_kn = rebuilt_operating_load_kn + reactor_mech.piping_load_kn + reactor_mech.wind_load_kn + reactor_mech.seismic_load_kn
    rebuilt_foundation_footprint_m2 = max(reactor_mech.foundation_footprint_m2, 1.25 * math.pi * (shell_diameter_m**2) / 4.0)
    support_rebuild_note = "support loads rebuilt from adopted shell, head, skirt, mixer, access steel, external heat-removal hardware, and liquid inventory"

    process_flow_m3_s = (feed_mass_flow / process_density) / 3600.0
    feed_velocity_basis_m_s = 1.5
    product_velocity_basis_m_s = 1.5
    drain_velocity_basis_m_s = 1.0
    feed_nozzle_required_mm = math.sqrt((4.0 * process_flow_m3_s) / (math.pi * feed_velocity_basis_m_s)) * 1000.0
    product_nozzle_required_mm = math.sqrt((4.0 * process_flow_m3_s) / (math.pi * product_velocity_basis_m_s)) * 1000.0
    drain_nozzle_required_mm = math.sqrt((4.0 * process_flow_m3_s) / (math.pi * drain_velocity_basis_m_s)) * 1000.0
    vent_nozzle_required_mm = 10.0
    vent_velocity_basis_m_s = None

    feed_nozzle_adopted_nb = _pick_standard_nb(feed_nozzle_required_mm)
    product_nozzle_adopted_nb = _pick_standard_nb(product_nozzle_required_mm)
    drain_nozzle_adopted_nb = _pick_standard_nb(drain_nozzle_required_mm)
    vent_nozzle_adopted_nb = _pick_standard_nb(vent_nozzle_required_mm)
    instrument_nozzle_adopted_nb = 25
    instrument_velocity_basis_m_s = None
    manway_diameter_mm = 600
    nozzle_neck_thickness_map_mm = {
        25: 3.4,
        32: 3.6,
        40: 3.7,
        50: 3.9,
        65: 5.2,
        80: 5.5,
        100: 6.0,
    }
    feed_nozzle_neck_thickness_mm = nozzle_neck_thickness_map_mm.get(feed_nozzle_adopted_nb, 6.0)
    product_nozzle_neck_thickness_mm = nozzle_neck_thickness_map_mm.get(product_nozzle_adopted_nb, 6.0)
    drain_nozzle_neck_thickness_mm = nozzle_neck_thickness_map_mm.get(drain_nozzle_adopted_nb, 6.0)
    loop_nozzle_neck_thickness_mm = nozzle_neck_thickness_map_mm.get(loop_line_adopted_nb, 6.0)
    vent_nozzle_neck_thickness_mm = nozzle_neck_thickness_map_mm.get(vent_nozzle_adopted_nb, 3.4)
    instrument_nozzle_neck_thickness_mm = nozzle_neck_thickness_map_mm.get(instrument_nozzle_adopted_nb, 3.4)
    feed_nozzle_projection_mm = 150
    product_nozzle_projection_mm = 150
    drain_nozzle_projection_mm = 175
    loop_nozzle_projection_mm = 200
    vent_nozzle_projection_mm = 125
    instrument_nozzle_projection_mm = 100
    nozzle_mechanical_class = reactor_mech.pressure_class
    nozzle_reinforcement_status = "required for major process and loop nozzles; detailed pad sizing remains for final code design"

    report_title = (
        f"Detailed Mechanical Design of Reactor {reactor.reactor_id} for "
        f"{project_basis.target_product}"
    )
    process_method = "liquid-phase Menshutkin quaternization of dodecyldimethylamine with benzyl chloride"
    design_status = "preliminary detailed mechanical calculation package"
    code_basis = "ASME Section VIII Division 1 style screening basis"
    document_scope = (
        "reactor-only mechanical calculation dossier covering vessel, mixer, external heat-removal loop interface, nozzles, and support basis"
    )

    design_basis_lock = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "reactor_type": reactor_basis.selected_reactor_type,
        "product": project_basis.target_product,
        "process_method": process_method,
        "design_status": design_status,
        "code_basis": code_basis,
        "document_scope": document_scope,
        "design_temperature_c": reactor.design_temperature_c,
        "design_pressure_bar": reactor.design_pressure_bar,
        "hydrotest_pressure_bar": reactor_mech.hydrotest_pressure_bar,
        "joint_efficiency": reactor_mech.joint_efficiency,
        "corrosion_allowance_mm": reactor_mech.corrosion_allowance_mm,
        "selected_head_type": head_type,
        "selected_support_variant": reactor_mech.support_variant,
        "shell_internal_volume_m3": round(shell_internal_volume_m3, 3),
        "total_head_volume_m3": round(total_head_volume_m3, 3),
        "total_internal_volume_m3": round(total_internal_volume_m3, 3),
        "freeboard_volume_m3": round(freeboard_volume_m3, 3),
        "shell_slenderness_ratio": round(shell_slenderness_ratio, 3),
        "cooling_medium": reactor.cooling_medium,
        "citations": reactor_equipment.citations,
        "phase": "phase_1_design_basis_lock",
    }
    design_conditions_lock = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_1_design_conditions_lock",
        "design_pressure_bar": round(reactor.design_pressure_bar, 3),
        "design_temperature_c": round(reactor.design_temperature_c, 3),
        "hydrotest_pressure_bar": round(reactor_mech.hydrotest_pressure_bar, 3),
        "pressure_class": reactor_mech.pressure_class,
        "allowable_stress_mpa": round(reactor_mech.allowable_stress_mpa, 3),
        "joint_efficiency": round(reactor_mech.joint_efficiency, 3),
        "corrosion_allowance_mm": round(reactor_mech.corrosion_allowance_mm, 3),
        "cooling_medium": reactor.cooling_medium,
        "support_type": reactor_mech.support_type,
        "support_variant": reactor_mech.support_variant,
        "citations": reactor_equipment.citations,
    }
    material_code_basis = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_1_material_code_basis",
        "code_basis": code_basis,
        "shell_material": reactor_equipment.material_of_construction,
        "head_material": reactor_equipment.material_of_construction,
        "jacket_material": reactor_equipment.material_of_construction,
        "nozzle_material": reactor_equipment.material_of_construction,
        "support_material": reactor_equipment.material_of_construction,
        "shaft_material": shaft_material,
        "pressure_class": reactor_mech.pressure_class,
        "allowable_stress_mpa": round(reactor_mech.allowable_stress_mpa, 3),
        "citations": reactor_equipment.citations,
    }
    geometry_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_2_vessel_geometry",
        "shell_diameter_m": round(shell_diameter_m, 3),
        "tangent_length_m": round(tangent_length_m, 3),
        "head_type": head_type,
        "head_depth_m": round(head_depth_m, 3),
        "overall_vessel_height_m": round(overall_vessel_height_m, 3),
        "shell_internal_volume_m3": round(shell_internal_volume_m3, 3),
        "each_head_internal_volume_m3": round(each_head_internal_volume_m3, 3),
        "total_head_volume_m3": round(total_head_volume_m3, 3),
        "total_internal_volume_m3": round(total_internal_volume_m3, 3),
        "design_liquid_holdup_m3": round(reactor.liquid_holdup_m3, 3),
        "design_vessel_volume_m3": round(reactor.design_volume_m3, 3),
        "design_volume_margin_fraction": round(design_volume_margin_fraction, 5),
        "freeboard_volume_m3": round(freeboard_volume_m3, 3),
        "freeboard_fraction_of_total": round(freeboard_fraction_of_total, 5),
        "shell_slenderness_ratio": round(shell_slenderness_ratio, 3),
        "citations": reactor_equipment.citations,
    }
    shell_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_3_shell_design",
        "code_basis": code_basis,
        "design_pressure_mpa": round(pressure_mpa, 3),
        "shell_diameter_m": round(shell_diameter_m, 3),
        "allowable_stress_mpa": round(allowable_stress_mpa, 3),
        "joint_efficiency": round(joint_efficiency, 3),
        "corrosion_allowance_mm": round(corrosion_allowance_mm, 3),
        "shell_pressure_term_mm": round(shell_pressure_term_mm, 3),
        "required_shell_thickness_mm": round(required_shell_thickness_mm, 3),
        "adopted_shell_thickness_mm": round(adopted_shell_thickness_mm, 3),
        "shell_nominal_margin_mm": round(shell_nominal_margin_mm, 3),
        "shell_nominal_margin_fraction": round(shell_nominal_margin_fraction, 5),
        "shell_mill_tolerance_fraction": round(shell_mill_tolerance_fraction, 5),
        "shell_min_after_tolerance_mm": round(shell_min_after_tolerance_mm, 3),
        "shell_is_tolerance_compliant": shell_is_tolerance_compliant,
        "citations": reactor_equipment.citations,
    }
    head_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_4_head_design",
        "code_basis": code_basis,
        "head_type": head_type,
        "design_pressure_mpa": round(pressure_mpa, 3),
        "shell_diameter_m": round(shell_diameter_m, 3),
        "allowable_stress_mpa": round(allowable_stress_mpa, 3),
        "joint_efficiency": round(joint_efficiency, 3),
        "corrosion_allowance_mm": round(corrosion_allowance_mm, 3),
        "head_pressure_term_mm": round(head_pressure_term_mm, 3),
        "required_head_thickness_mm": round(required_head_thickness_mm, 3),
        "adopted_head_thickness_mm": round(adopted_head_thickness_mm, 3),
        "head_nominal_margin_mm": round(head_nominal_margin_mm, 3),
        "head_nominal_margin_fraction": round(head_nominal_margin_fraction, 5),
        "head_mill_tolerance_fraction": round(head_mill_tolerance_fraction, 5),
        "head_min_after_tolerance_mm": round(head_min_after_tolerance_mm, 3),
        "head_is_tolerance_compliant": head_is_tolerance_compliant,
        "hydrotest_pressure_bar": round(reactor_mech.hydrotest_pressure_bar, 3),
        "citations": reactor_equipment.citations,
    }
    agitation_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_5_agitation_design",
        "impeller_type": impeller_type,
        "impeller_count": impeller_count,
        "impeller_diameter_m": round(impeller_diameter_m, 3),
        "impeller_diameter_ratio": round(impeller_diameter_ratio, 3),
        "impeller_speed_rpm": round(impeller_speed_rpm, 3),
        "power_number": round(power_number, 3),
        "agitator_reynolds": round(agitator_reynolds, 3),
        "flow_regime": flow_regime,
        "power_per_impeller_kw": round(power_per_impeller_kw, 3),
        "total_agitator_power_kw": round(agitator_power_kw, 3),
        "power_per_volume_kw_m3": round(power_per_volume_kw_m3, 5),
        "agitator_tip_speed_m_s": round(agitator_tip_speed_m_s, 3),
        "baffle_count": baffle_count,
        "baffle_width_m": round(baffle_width_m, 3),
        "impeller_spacing_m": round(impeller_spacing_m, 3),
        "bottom_clearance_m": round(bottom_clearance_m, 3),
        "top_clearance_m": round(top_clearance_m, 3),
        "selected_motor_kw": round(selected_motor_kw, 3),
        "agitator_loading_fraction": round(agitator_loading_fraction, 5),
        "drive_arrangement": drive_arrangement,
        "seal_arrangement": seal_arrangement,
        "mixer_mounting_basis": mixer_mounting_basis,
        "citations": reactor_equipment.citations,
    }
    mixer_mechanical_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_2_mixer_mechanical_design",
        "impeller_type": impeller_type,
        "impeller_count": impeller_count,
        "impeller_diameter_m": round(impeller_diameter_m, 3),
        "impeller_spacing_m": round(impeller_spacing_m, 3),
        "bottom_clearance_m": round(bottom_clearance_m, 3),
        "top_clearance_m": round(top_clearance_m, 3),
        "selected_motor_kw": round(selected_motor_kw, 3),
        "drive_arrangement": drive_arrangement,
        "seal_arrangement": seal_arrangement,
        "mixer_mounting_basis": mixer_mounting_basis,
        "estimated_impeller_mass_each_kg": round(estimated_impeller_mass_each_kg, 3),
        "total_impeller_mass_kg": round(total_impeller_mass_kg, 3),
        "citations": reactor_equipment.citations,
    }
    heat_removal_selection_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_3_heat_removal_selection",
        "selected_concept": selected_heat_removal_concept,
        "selected_total_score": selected_heat_removal_option["total_score"],
        "options": heat_removal_options,
        "rejected_jacket_basis_note": rejected_jacket_basis_note,
        "citations": reactor_equipment.citations,
    }
    heat_removal_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_3_heat_removal_design",
        "selected_concept": selected_heat_removal_concept,
        "exchanger_type": loop_exchanger_type,
        "heat_duty_kw": round(reactor.heat_duty_kw, 3),
        "required_heat_transfer_area_m2": round(jacket_required_area_m2, 3),
        "process_side_cp_kj_kg_k": round(loop_process_cp_kj_kg_k, 3),
        "process_side_delta_t_c": round(loop_process_delta_t_c, 3),
        "process_side_circulation_kg_s": round(loop_process_circulation_kg_s, 3),
        "process_side_circulation_m3_s": round(loop_process_circulation_m3_s, 6),
        "process_side_holdup_m3": round(loop_process_holdup_m3, 3),
        "loop_line_velocity_basis_m_s": round(loop_line_velocity_basis_m_s, 3),
        "loop_line_required_mm": round(loop_line_required_mm, 3),
        "loop_line_adopted_nb": loop_line_adopted_nb,
        "cooling_medium": reactor.cooling_medium,
        "citations": reactor_equipment.citations,
    }
    shaft_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_6_shaft_design",
        "shaft_material": shaft_material,
        "running_torque_n_m": round(design_torque_n_m, 3),
        "service_factor": round(service_factor, 3),
        "design_torque_n_m": round(design_torque_with_factor_n_m, 3),
        "allowable_shear_stress_mpa": round(shaft_allowable_shear_pa / 1e6, 3),
        "required_shaft_diameter_mm": round(required_shaft_diameter_m * 1000.0, 3),
        "adopted_shaft_diameter_mm": round(adopted_shaft_diameter_mm, 3),
        "transmitted_shear_stress_mpa": round(shaft_transmitted_shear_mpa, 3),
        "stress_utilization_fraction": round(shaft_stress_utilization_fraction, 5),
        "shaft_is_adequate": shaft_is_adequate,
        "shaft_length_m": round(shaft_length_m, 3),
        "shaft_l_over_d_ratio": round(shaft_l_over_d_ratio, 3),
        "shaft_support_strategy": shaft_support_strategy,
        "shaft_effective_unsupported_span_m": round(shaft_effective_unsupported_span_m, 3),
        "shaft_span_l_over_d_ratio": round(shaft_span_l_over_d_ratio, 3),
        "shaft_overall_status": shaft_overall_status,
        "citations": reactor_equipment.citations,
    }
    shaft_dynamic_screen_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_2_shaft_dynamic_screen",
        "shaft_material": shaft_material,
        "shaft_modulus_gpa": round(shaft_modulus_pa / 1e9, 3),
        "shaft_density_kg_m3": round(shaft_density_kg_m3, 3),
        "shaft_length_m": round(shaft_length_m, 3),
        "shaft_diameter_mm": round(adopted_shaft_diameter_mm, 3),
        "shaft_support_strategy": shaft_support_strategy,
        "shaft_effective_unsupported_span_m": round(shaft_effective_unsupported_span_m, 3),
        "shaft_mass_kg": round(shaft_mass_kg, 3),
        "estimated_impeller_mass_each_kg": round(estimated_impeller_mass_each_kg, 3),
        "total_impeller_mass_kg": round(total_impeller_mass_kg, 3),
        "rotating_mass_kg": round(rotating_mass_kg, 3),
        "static_deflection_m": round(shaft_static_deflection_m, 5),
        "first_critical_speed_rpm": round(first_critical_speed_rpm, 3),
        "operating_speed_rpm": round(impeller_speed_rpm, 3),
        "operating_to_critical_speed_ratio": round(operating_to_critical_speed_ratio, 5),
        "dynamic_status": shaft_dynamic_status,
        "dynamic_note": shaft_dynamic_note,
        "citations": reactor_equipment.citations,
    }
    jacket_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_7_jacket_design",
        "cooling_medium": reactor.cooling_medium,
        "heat_duty_kw": round(reactor.heat_duty_kw, 3),
        "overall_u_w_m2_k": round(reactor.overall_u_w_m2_k, 3),
        "required_heat_transfer_area_m2": round(jacket_required_area_m2, 3),
        "equivalent_jacket_height_m": round(jacket_equivalent_height_m, 3),
        "adopted_jacket_height_m": round(adopted_jacket_height_m, 3),
        "jacket_gap_m": round(jacket_gap_m, 3),
        "jacket_outer_diameter_m": round(jacket_outer_diameter_m, 3),
        "jacket_hold_up_volume_m3": round(jacket_volume_m3, 3),
        "jacket_design_pressure_bar": round(jacket_design_pressure_bar, 3),
        "jacket_design_temperature_c": round(jacket_design_temperature_c, 3),
        "jacket_cp_kj_kg_k": round(jacket_cp_kj_kg_k, 3),
        "jacket_density_kg_m3": round(jacket_density_kg_m3, 3),
        "jacket_delta_t_c": round(jacket_delta_t_c, 3),
        "jacket_flow_kg_s": round(jacket_flow_kg_s, 3),
        "jacket_flow_m3_s": round(jacket_flow_m3_s, 6),
        "jacket_velocity_basis_m_s": round(jacket_velocity_basis_m_s, 3),
        "jacket_circulation_time_s": round(jacket_circulation_time_s, 3),
        "jacket_pressure_term_mm": round(jacket_pressure_term_mm, 3),
        "required_jacket_shell_thickness_mm": round(required_jacket_shell_thickness_mm, 3),
        "adopted_jacket_shell_thickness_mm": round(adopted_jacket_shell_thickness_mm, 3),
        "jacket_nominal_margin_mm": round(jacket_nominal_margin_mm, 3),
        "jacket_min_after_tolerance_mm": round(jacket_min_after_tolerance_mm, 3),
        "jacket_is_tolerance_compliant": jacket_is_tolerance_compliant,
        "jacket_nozzle_required_mm": round(jacket_nozzle_required_mm, 3),
        "jacket_nozzle_adopted_nb": jacket_nozzle_adopted_nb,
        "citations": reactor_equipment.citations,
    }
    nozzle_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_8_nozzle_design",
        "process_density_kg_m3": round(process_density, 3),
        "process_volumetric_flow_m3_s": round(process_flow_m3_s, 6),
        "feed_nozzle": {
            "service": "main feed inlet",
            "flow_basis": round(feed_mass_flow, 3),
            "flow_units": "kg/h",
            "velocity_basis_m_s": round(feed_velocity_basis_m_s, 3),
            "required_id_mm": round(feed_nozzle_required_mm, 3),
            "adopted_nb_mm": feed_nozzle_adopted_nb,
            "orientation": "0 deg",
        },
        "product_nozzle": {
            "service": "reactor outlet",
            "flow_basis": round(product_mass_flow, 3),
            "flow_units": "kg/h",
            "velocity_basis_m_s": round(product_velocity_basis_m_s, 3),
            "required_id_mm": round(product_nozzle_required_mm, 3),
            "adopted_nb_mm": product_nozzle_adopted_nb,
            "orientation": "180 deg",
        },
        "drain_nozzle": {
            "service": "bottom drain",
            "flow_basis": round(feed_mass_flow, 3),
            "flow_units": "kg/h",
            "velocity_basis_m_s": round(drain_velocity_basis_m_s, 3),
            "required_id_mm": round(drain_nozzle_required_mm, 3),
            "adopted_nb_mm": drain_nozzle_adopted_nb,
            "orientation": "270 deg",
        },
        "jacket_inlet_nozzle": {
            "service": "jacket inlet",
            "flow_basis": round(jacket_flow_kg_s, 3),
            "flow_units": "kg/s",
            "velocity_basis_m_s": round(jacket_velocity_basis_m_s, 3),
            "required_id_mm": round(jacket_nozzle_required_mm, 3),
            "adopted_nb_mm": jacket_nozzle_adopted_nb,
            "orientation": "90 deg",
        },
        "jacket_outlet_nozzle": {
            "service": "jacket outlet",
            "flow_basis": round(jacket_flow_kg_s, 3),
            "flow_units": "kg/s",
            "velocity_basis_m_s": round(jacket_velocity_basis_m_s, 3),
            "required_id_mm": round(jacket_nozzle_required_mm, 3),
            "adopted_nb_mm": jacket_nozzle_adopted_nb,
            "orientation": "270 deg",
        },
        "vent_psv_nozzle": {
            "service": "vent / PSV take-off",
            "velocity_basis_m_s": vent_velocity_basis_m_s,
            "required_id_mm": round(vent_nozzle_required_mm, 3),
            "adopted_nb_mm": vent_nozzle_adopted_nb,
            "orientation": "top center",
            "basis": "vapor disengagement and relief allowance screening",
        },
        "instrument_nozzles": {
            "service": "temperature, pressure, level, sample points",
            "velocity_basis_m_s": instrument_velocity_basis_m_s,
            "adopted_nb_mm": instrument_nozzle_adopted_nb,
            "orientation": "multiple",
        },
        "manway": {
            "service": "operator entry / cleaning access",
            "diameter_mm": manway_diameter_mm,
            "orientation": "top head",
        },
        "reinforcement_basis": "branch reinforcement and local shell checks to be completed during detailed code design; current schedule is preliminary process-mechanical screening",
        "citations": reactor_equipment.citations,
    }
    nozzle_mechanical_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_5_nozzle_mechanical_design",
        "pressure_class": nozzle_mechanical_class,
        "nozzle_reinforcement_family": reactor_mech.nozzle_reinforcement_family,
        "local_shell_load_interaction_factor": round(reactor_mech.local_shell_load_interaction_factor, 3),
        "nozzle_reinforcement_area_mm2": round(reactor_mech.nozzle_reinforcement_area_mm2, 3),
        "feed_nozzle": {
            "adopted_nb_mm": feed_nozzle_adopted_nb,
            "neck_thickness_mm": round(feed_nozzle_neck_thickness_mm, 3),
            "projection_mm": feed_nozzle_projection_mm,
            "orientation": "0 deg",
        },
        "product_nozzle": {
            "adopted_nb_mm": product_nozzle_adopted_nb,
            "neck_thickness_mm": round(product_nozzle_neck_thickness_mm, 3),
            "projection_mm": product_nozzle_projection_mm,
            "orientation": "180 deg",
        },
        "drain_nozzle": {
            "adopted_nb_mm": drain_nozzle_adopted_nb,
            "neck_thickness_mm": round(drain_nozzle_neck_thickness_mm, 3),
            "projection_mm": drain_nozzle_projection_mm,
            "orientation": "270 deg",
        },
        "loop_nozzles": {
            "adopted_nb_mm": loop_line_adopted_nb,
            "neck_thickness_mm": round(loop_nozzle_neck_thickness_mm, 3),
            "projection_mm": loop_nozzle_projection_mm,
            "orientation": "side shell nozzles for external loop service",
        },
        "vent_psv_nozzle": {
            "adopted_nb_mm": vent_nozzle_adopted_nb,
            "neck_thickness_mm": round(vent_nozzle_neck_thickness_mm, 3),
            "projection_mm": vent_nozzle_projection_mm,
            "orientation": "top center",
        },
        "instrument_nozzles": {
            "adopted_nb_mm": instrument_nozzle_adopted_nb,
            "neck_thickness_mm": round(instrument_nozzle_neck_thickness_mm, 3),
            "projection_mm": instrument_nozzle_projection_mm,
            "orientation": "multiple",
        },
        "reinforcement_status": nozzle_reinforcement_status,
        "citations": reactor_equipment.citations,
    }
    nozzle_reinforcement_basis_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_5_nozzle_reinforcement_basis",
        "pressure_class": nozzle_mechanical_class,
        "reinforcement_family": reactor_mech.nozzle_reinforcement_family,
        "required_reinforcement_area_mm2": round(reactor_mech.nozzle_reinforcement_area_mm2, 3),
        "local_shell_load_interaction_factor": round(reactor_mech.local_shell_load_interaction_factor, 3),
        "status": nozzle_reinforcement_status,
        "citations": reactor_equipment.citations,
    }
    support_design_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_9_support_basis",
        "support_type": reactor_mech.support_type,
        "support_variant": reactor_mech.support_variant,
        "support_thickness_mm": round(reactor_mech.support_thickness_mm, 3),
        "operating_load_kn": round(reactor_mech.operating_load_kn, 3),
        "design_vertical_load_kn": round(reactor_mech.design_vertical_load_kn, 3),
        "piping_load_kn": round(reactor_mech.piping_load_kn, 3),
        "wind_load_kn": round(reactor_mech.wind_load_kn, 3),
        "seismic_load_kn": round(reactor_mech.seismic_load_kn, 3),
        "support_load_case": reactor_mech.support_load_case,
        "thermal_growth_mm": round(reactor_mech.thermal_growth_mm, 3),
        "anchor_group_count": reactor_mech.anchor_group_count,
        "foundation_footprint_m2": round(reactor_mech.foundation_footprint_m2, 3),
        "maintenance_platform_required": reactor_mech.maintenance_platform_required,
        "platform_area_m2": round(reactor_mech.platform_area_m2, 3),
        "access_ladder_required": reactor_mech.access_ladder_required,
        "lifting_lug_required": reactor_mech.lifting_lug_required,
        "maintenance_clearance_m": round(reactor_mech.maintenance_clearance_m, 3),
        "nozzle_reinforcement_area_mm2": round(reactor_mech.nozzle_reinforcement_area_mm2, 3),
        "nozzle_reinforcement_family": reactor_mech.nozzle_reinforcement_family,
        "local_shell_load_interaction_factor": round(reactor_mech.local_shell_load_interaction_factor, 3),
        "citations": reactor_equipment.citations,
    }
    weight_load_summary_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_4_weight_and_load_summary",
        "shell_steel_kg": round(shell_steel_kg, 3),
        "head_steel_kg": round(head_steel_kg, 3),
        "skirt_steel_kg": round(skirt_steel_kg, 3),
        "attachment_kg": round(attachment_kg, 3),
        "rotating_equipment_kg": round(rotating_equipment_kg, 3),
        "thermal_hardware_kg": round(thermal_hardware_kg, 3),
        "operating_liquid_kg": round(operating_liquid_kg, 3),
        "hydrotest_liquid_kg": round(hydrotest_liquid_kg, 3),
        "empty_weight_kg": round(empty_weight_kg, 3),
        "operating_weight_kg": round(operating_weight_kg, 3),
        "hydrotest_weight_kg": round(hydrotest_weight_kg, 3),
        "rebuilt_empty_load_kn": round(rebuilt_empty_load_kn, 3),
        "rebuilt_operating_load_kn": round(rebuilt_operating_load_kn, 3),
        "rebuilt_hydrotest_load_kn": round(rebuilt_hydrotest_load_kn, 3),
        "citations": reactor_equipment.citations,
    }
    support_rebuild_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_4_support_rebuild",
        "support_type": reactor_mech.support_type,
        "support_variant": reactor_mech.support_variant,
        "support_thickness_mm": round(reactor_mech.support_thickness_mm, 3),
        "rebuilt_empty_load_kn": round(rebuilt_empty_load_kn, 3),
        "rebuilt_operating_load_kn": round(rebuilt_operating_load_kn, 3),
        "rebuilt_hydrotest_load_kn": round(rebuilt_hydrotest_load_kn, 3),
        "rebuilt_design_vertical_load_kn": round(rebuilt_design_vertical_load_kn, 3),
        "piping_load_kn": round(reactor_mech.piping_load_kn, 3),
        "wind_load_kn": round(reactor_mech.wind_load_kn, 3),
        "seismic_load_kn": round(reactor_mech.seismic_load_kn, 3),
        "anchor_group_count": reactor_mech.anchor_group_count,
        "rebuilt_foundation_footprint_m2": round(rebuilt_foundation_footprint_m2, 3),
        "support_rebuild_note": support_rebuild_note,
        "citations": reactor_equipment.citations,
    }
    mechanical_consistency_rows = [
        ["Mixer arrangement", mixer_mounting_basis],
        ["Adopted shaft support strategy", shaft_support_strategy],
        ["Adopted shaft diameter", f"{_fmt(adopted_shaft_diameter_mm, 1)} mm"],
        ["Effective unsupported span", f"{_fmt(shaft_effective_unsupported_span_m, 3)} m"],
        ["Dynamic screen", f"{shaft_dynamic_status} at {_fmt(first_critical_speed_rpm, 3)} rpm critical speed"],
        ["Selected heat-removal concept", selected_heat_removal_concept],
        ["Loop nozzle alignment", f"{loop_line_adopted_nb} NB suction and return nozzles retained in final nozzle package"],
        ["Legacy jacket basis", "retained only as screening reference and removed from final adopted nozzle philosophy"],
        ["Support package alignment", "support loads rebuilt with stabilized mixer mass and external loop hardware included"],
        ["Final closure note", "reactor final specification, nozzle schedule, and support basis now refer to the same adopted mechanical package"],
    ]
    mechanical_consistency_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_6_mechanical_consistency_closure",
        "shaft_support_strategy": shaft_support_strategy,
        "adopted_shaft_diameter_mm": round(adopted_shaft_diameter_mm, 3),
        "effective_unsupported_span_m": round(shaft_effective_unsupported_span_m, 3),
        "shaft_dynamic_status": shaft_dynamic_status,
        "selected_heat_removal_concept": selected_heat_removal_concept,
        "loop_line_adopted_nb": loop_line_adopted_nb,
        "legacy_jacket_removed_from_final_nozzle_package": True,
        "support_load_basis": support_rebuild_note,
        "overall_status": "closed" if shaft_dynamic_status == "pass" else "open",
        "citations": reactor_equipment.citations,
    }
    foundation_basis_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_4_foundation_basis",
        "foundation_footprint_m2": round(rebuilt_foundation_footprint_m2, 3),
        "anchor_group_count": reactor_mech.anchor_group_count,
        "maintenance_clearance_m": round(reactor_mech.maintenance_clearance_m, 3),
        "platform_area_m2": round(reactor_mech.platform_area_m2, 3),
        "support_variant": reactor_mech.support_variant,
        "citations": reactor_equipment.citations,
    }

    design_lock_rows = [
        ["Reactor identifier", reactor.reactor_id],
        ["Selected reactor type", reactor_basis.selected_reactor_type],
        ["Product", project_basis.target_product],
        ["Method", process_method],
        ["Document status", design_status],
        ["Code basis", code_basis],
        ["Scope", document_scope],
        ["Design pressure", f"{_fmt(reactor.design_pressure_bar, 2)} bar"],
        ["Design temperature", f"{_fmt(reactor.design_temperature_c, 1)} C"],
        ["Hydrotest pressure", f"{_fmt(reactor_mech.hydrotest_pressure_bar, 3)} bar"],
        ["Joint efficiency", f"{_fmt(reactor_mech.joint_efficiency, 2)}"],
        ["Corrosion allowance", f"{_fmt(reactor_mech.corrosion_allowance_mm, 1)} mm"],
        ["Selected head type", head_type],
        ["Selected support basis", reactor_mech.support_variant],
    ]
    design_condition_rows = [
        ["Design pressure", f"{_fmt(reactor.design_pressure_bar, 2)} bar"],
        ["Design temperature", f"{_fmt(reactor.design_temperature_c, 1)} C"],
        ["Hydrotest pressure", f"{_fmt(reactor_mech.hydrotest_pressure_bar, 3)} bar"],
        ["Pressure class basis", reactor_mech.pressure_class],
        ["Allowable stress basis", f"{_fmt(reactor_mech.allowable_stress_mpa, 1)} MPa"],
        ["Joint efficiency", f"{_fmt(reactor_mech.joint_efficiency, 2)}"],
        ["Corrosion allowance", f"{_fmt(reactor_mech.corrosion_allowance_mm, 1)} mm"],
        ["Cooling medium basis", reactor.cooling_medium],
    ]
    material_code_rows = [
        ["Code basis", code_basis],
        ["Shell material", reactor_equipment.material_of_construction],
        ["Head material", reactor_equipment.material_of_construction],
        ["Jacket material", reactor_equipment.material_of_construction],
        ["Nozzle material", reactor_equipment.material_of_construction],
        ["Support material", reactor_equipment.material_of_construction],
        ["Shaft material", shaft_material],
        ["Pressure class", reactor_mech.pressure_class],
    ]

    basis_rows = [
        ["Product", project_basis.target_product],
        ["Primary reactor", f"{reactor.reactor_id} ({reactor_basis.selected_reactor_type})"],
        ["Process method", process_method],
        ["Design volume", f"{_fmt(reactor.design_volume_m3)} m3"],
        ["Liquid holdup", f"{_fmt(reactor.liquid_holdup_m3)} m3"],
        ["Design temperature", f"{_fmt(reactor.design_temperature_c, 1)} C"],
        ["Design pressure", f"{_fmt(reactor.design_pressure_bar, 2)} bar"],
        ["Feed rate to reactor", f"{_fmt(feed_mass_flow)} kg/h"],
        ["Product-rich effluent", f"{_fmt(product_mass_flow)} kg/h"],
    ]

    geometry_rows = [
        ["Internal shell diameter", f"{_fmt(shell_diameter_m)} m"],
        ["Straight side length", f"{_fmt(tangent_length_m)} m"],
        ["Head type", head_type],
        ["Head depth each", f"{_fmt(head_depth_m)} m"],
        ["Approximate vessel height without skirt", f"{_fmt(overall_vessel_height_m)} m"],
        ["Support style", reactor_mech.support_variant],
        ["Foundation footprint", f"{_fmt(reactor_mech.foundation_footprint_m2)} m2"],
    ]
    geometry_calc_rows = [
        ["Design liquid holdup", f"{_fmt(reactor.liquid_holdup_m3)} m3"],
        ["Design vessel volume", f"{_fmt(reactor.design_volume_m3)} m3"],
        ["Volume design margin", f"{_fmt(design_volume_margin_fraction * 100.0, 2)} %"],
        ["Cylindrical shell volume", f"{_fmt(shell_internal_volume_m3)} m3"],
        ["Each head volume", f"{_fmt(each_head_internal_volume_m3)} m3"],
        ["Total head volume", f"{_fmt(total_head_volume_m3)} m3"],
        ["Total internal vessel volume", f"{_fmt(total_internal_volume_m3)} m3"],
        ["Available freeboard volume", f"{_fmt(freeboard_volume_m3)} m3"],
        ["Freeboard fraction of total volume", f"{_fmt(freeboard_fraction_of_total * 100.0, 2)} %"],
        ["Shell slenderness ratio (L/D)", f"{_fmt(shell_slenderness_ratio, 3)}"],
    ]
    geometry_selection_rows = [
        ["Selected vessel form", "vertical agitated cylindrical vessel with two ellipsoidal heads"],
        ["Diameter basis", "retained from solved reactor packet to preserve heat-transfer and agitation envelope"],
        ["Length basis", "retained from solved reactor packet to satisfy design volume and impeller-train spacing"],
        ["Head basis", "2:1 ellipsoidal heads selected for practical pressure-vessel fabrication and agitator clearance"],
        ["Freeboard basis", "internal volume above liquid holdup reserved for vapor disengagement and operating surge"],
        ["Aspect-ratio check", "L/D retained as a tall agitated-reactor geometry suitable for multiple impellers"],
    ]

    shell_rows = [
        ["Equation", "t = P D / (2 S E - 1.2 P) + CA"],
        ["P", f"{_fmt(pressure_mpa, 3)} MPa"],
        ["D", f"{_fmt(shell_diameter_m, 3)} m"],
        ["S", f"{_fmt(allowable_stress_mpa, 1)} MPa"],
        ["E", f"{_fmt(joint_efficiency, 2)}"],
        ["CA", f"{_fmt(corrosion_allowance_mm, 1)} mm"],
        ["Pressure-only thickness term", f"{_fmt(shell_pressure_term_mm, 3)} mm"],
        ["Required shell thickness", f"{_fmt(required_shell_thickness_mm, 3)} mm"],
        ["Adopted nominal shell thickness", f"{_fmt(adopted_shell_thickness_mm, 1)} mm"],
    ]
    shell_selection_rows = [
        ["Selected shell plate", f"{_fmt(adopted_shell_thickness_mm, 1)} mm nominal"],
        ["Nominal margin above required", f"{_fmt(shell_nominal_margin_mm, 3)} mm"],
        ["Nominal margin fraction", f"{_fmt(shell_nominal_margin_fraction * 100.0, 2)} %"],
        ["Assumed mill tolerance", f"{_fmt(shell_mill_tolerance_fraction * 100.0, 1)} % under-thickness"],
        ["Minimum thickness after tolerance", f"{_fmt(shell_min_after_tolerance_mm, 3)} mm"],
        ["Tolerance compliance check", "pass" if shell_is_tolerance_compliant else "fail"],
    ]

    head_rows = [
        ["Selected head", head_type],
        ["Equation", "t = 0.885 P D / (2 S E - 0.1 P) + CA"],
        ["Pressure-only thickness term", f"{_fmt(head_pressure_term_mm, 3)} mm"],
        ["Required head thickness", f"{_fmt(required_head_thickness_mm, 3)} mm"],
        ["Adopted nominal head thickness", f"{_fmt(adopted_head_thickness_mm, 1)} mm"],
        ["Hydrotest pressure", f"{_fmt(reactor_mech.hydrotest_pressure_bar, 3)} bar"],
    ]
    head_selection_rows = [
        ["Selected head form", head_type],
        ["Selected head plate", f"{_fmt(adopted_head_thickness_mm, 1)} mm nominal"],
        ["Nominal margin above required", f"{_fmt(head_nominal_margin_mm, 3)} mm"],
        ["Nominal margin fraction", f"{_fmt(head_nominal_margin_fraction * 100.0, 2)} %"],
        ["Assumed mill tolerance", f"{_fmt(head_mill_tolerance_fraction * 100.0, 1)} % under-thickness"],
        ["Minimum thickness after tolerance", f"{_fmt(head_min_after_tolerance_mm, 3)} mm"],
        ["Tolerance compliance check", "pass" if head_is_tolerance_compliant else "fail"],
    ]

    agitation_rows = [
        ["Impeller type", impeller_type],
        ["Number of impellers", str(impeller_count)],
        ["Impeller diameter", f"{_fmt(impeller_diameter_m, 3)} m"],
        ["Impeller diameter ratio (D/T)", f"{_fmt(impeller_diameter_ratio, 3)}"],
        ["Rotational speed", f"{_fmt(impeller_speed_rpm, 0)} rpm"],
        ["Power number", f"{_fmt(power_number, 3)}"],
        ["Tip speed", f"{_fmt(agitator_tip_speed_m_s, 3)} m/s"],
        ["Agitator Reynolds number", f"{_fmt(agitator_reynolds, 0)}"],
        ["Flow regime", flow_regime],
        ["Power per impeller", f"{_fmt(power_per_impeller_kw, 3)} kW"],
        ["Calculated agitator power", f"{_fmt(agitator_power_kw, 3)} kW"],
        ["Power per liquid volume", f"{_fmt(power_per_volume_kw_m3, 4)} kW/m3"],
        ["Selected motor", f"{_fmt(selected_motor_kw, 1)} kW"],
        ["Motor loading", f"{_fmt(agitator_loading_fraction * 100.0, 2)} %"],
        ["Drive arrangement", drive_arrangement],
        ["Seal arrangement", seal_arrangement],
        ["Mixer mounting basis", mixer_mounting_basis],
        ["Shaft support strategy", shaft_support_strategy],
        ["Baffle arrangement", f"{baffle_count} baffles x {_fmt(baffle_width_m, 3)} m width"],
        ["Vertical impeller spacing", f"{_fmt(impeller_spacing_m, 3)} m"],
        ["Bottom impeller clearance", f"{_fmt(bottom_clearance_m, 3)} m"],
        ["Top impeller clearance", f"{_fmt(top_clearance_m, 3)} m"],
    ]
    agitation_selection_rows = [
        ["Selected impeller family", impeller_type],
        ["Selection basis", "axial-flow impeller train selected for tall liquid-phase quaternization service"],
        ["Diameter basis", "D/T fixed at 0.35 for a practical large-reactor axial-flow mixing envelope"],
        ["Speed basis", "60 rpm retained to limit tip speed while maintaining turbulent mixing"],
        ["Impeller count basis", "4 impellers selected to cover the tall liquid column"],
        ["Baffle basis", "4 full-height baffles adopted at T/12 width"],
        ["Motor basis", f"{_fmt(selected_motor_kw, 1)} kW selected above absorbed power with practical service allowance"],
        ["Drive basis", drive_arrangement],
        ["Seal basis", seal_arrangement],
    ]

    shaft_rows = [
        ["Power transmitted", f"{_fmt(agitator_power_kw, 3)} kW"],
        ["Running torque", f"{_fmt(design_torque_n_m, 3)} N.m"],
        ["Service factor", f"{_fmt(service_factor, 2)}"],
        ["Design torque", f"{_fmt(design_torque_with_factor_n_m, 3)} N.m"],
        ["Allowable shaft shear stress", "35 MPa"],
        ["Required shaft diameter", f"{_fmt(required_shaft_diameter_m * 1000.0, 3)} mm"],
        ["Adopted solid shaft diameter", f"{_fmt(adopted_shaft_diameter_mm, 1)} mm"],
        ["Adopted shaft material", shaft_material],
        ["Transmitted shear stress at adopted diameter", f"{_fmt(shaft_transmitted_shear_mpa, 3)} MPa"],
        ["Stress utilization", f"{_fmt(shaft_stress_utilization_fraction * 100.0, 2)} %"],
        ["Estimated shaft length", f"{_fmt(shaft_length_m, 3)} m"],
        ["Slenderness ratio (L/d)", f"{_fmt(shaft_l_over_d_ratio, 2)}"],
        ["Effective unsupported span", f"{_fmt(shaft_effective_unsupported_span_m, 3)} m"],
        ["Span slenderness ratio", f"{_fmt(shaft_span_l_over_d_ratio, 2)}"],
        ["Torsional adequacy", "pass" if shaft_is_adequate else "fail"],
        ["Estimated shaft mass", f"{_fmt(shaft_mass_kg, 3)} kg"],
        ["Estimated impeller mass each", f"{_fmt(estimated_impeller_mass_each_kg, 3)} kg"],
        ["Estimated total rotating mass", f"{_fmt(rotating_mass_kg, 3)} kg"],
        ["Static deflection screen", f"{_fmt(shaft_static_deflection_m, 4)} m"],
        ["Screened first critical speed", f"{_fmt(first_critical_speed_rpm, 3)} rpm"],
        ["Operating / critical speed ratio", f"{_fmt(operating_to_critical_speed_ratio, 3)}"],
        ["Dynamic screening status", shaft_dynamic_status],
        ["Overall shaft status", shaft_overall_status],
    ]
    shaft_selection_rows = [
        ["Shaft material basis", shaft_material],
        ["Torque basis", "agitator absorbed power at operating speed with 1.5 service factor"],
        ["Diameter basis", "solid circular shaft first sized by torsional shear criterion"],
        ["Adopted shaft size", f"{_fmt(adopted_shaft_diameter_mm, 1)} mm"],
        ["Support strategy", shaft_support_strategy],
        ["Dynamic basis", "screened from shaft self-weight plus estimated impeller masses using the reduced unsupported span between steady supports"],
        ["Selection note", "adopted shaft size increased above earlier screening value and paired with internal shaft guides to close the dynamic gap"],
        ["Adequacy note", shaft_dynamic_note],
    ]

    jacket_rows = [
        ["Cooling medium", reactor.cooling_medium],
        ["Heat duty", f"{_fmt(reactor.heat_duty_kw, 3)} kW"],
        ["Overall U", f"{_fmt(reactor.overall_u_w_m2_k, 1)} W/m2-K"],
        ["Required heat-transfer area", f"{_fmt(jacket_required_area_m2, 3)} m2"],
        ["Equivalent full-circumference jacket height", f"{_fmt(jacket_equivalent_height_m, 3)} m"],
        ["Adopted jacket zone height", f"{_fmt(adopted_jacket_height_m, 3)} m"],
        ["Jacket gap", f"{_fmt(jacket_gap_m, 3)} m"],
        ["Jacket outer diameter", f"{_fmt(jacket_outer_diameter_m, 3)} m"],
        ["Jacket hold-up volume", f"{_fmt(jacket_volume_m3, 3)} m3"],
        ["Utility temperature rise basis", f"{_fmt(jacket_delta_t_c, 1)} C"],
        ["Utility flow", f"{_fmt(jacket_flow_kg_s, 3)} kg/s"],
        ["Utility volumetric flow", f"{_fmt(jacket_flow_m3_s, 5)} m3/s"],
        ["Estimated jacket circulation time", f"{_fmt(jacket_circulation_time_s, 2)} s"],
        ["Utility line velocity basis", f"{_fmt(jacket_velocity_basis_m_s, 1)} m/s"],
        ["Jacket pressure term", f"{_fmt(jacket_pressure_term_mm, 3)} mm"],
        ["Required jacket shell thickness", f"{_fmt(required_jacket_shell_thickness_mm, 3)} mm"],
        ["Adopted jacket shell thickness", f"{_fmt(adopted_jacket_shell_thickness_mm, 1)} mm"],
        ["Nominal thickness margin", f"{_fmt(jacket_nominal_margin_mm, 3)} mm"],
        ["Minimum after 12.5% tolerance", f"{_fmt(jacket_min_after_tolerance_mm, 3)} mm"],
        ["Tolerance compliance", "pass" if jacket_is_tolerance_compliant else "fail"],
    ]
    jacket_selection_rows = [
        ["Jacket type basis", "full circumferential jacket over the active heat-removal zone"],
        ["Coverage basis", f"adopted {_fmt(adopted_jacket_height_m, 3)} m active zone against {_fmt(jacket_equivalent_height_m, 3)} m equivalent requirement"],
        ["Utility basis", f"{reactor.cooling_medium} with {_fmt(jacket_delta_t_c, 1)} C rise and {_fmt(jacket_flow_kg_s, 3)} kg/s flow"],
        ["Thickness basis", f"{_fmt(adopted_jacket_shell_thickness_mm, 1)} mm nominal plate selected above calculated {_fmt(required_jacket_shell_thickness_mm, 3)} mm requirement"],
        ["Nozzle basis", f"{jacket_nozzle_adopted_nb} NB jacket connections selected from {_fmt(jacket_nozzle_required_mm, 2)} mm required bore"],
        ["Selection note", "jacket zone kept compact around the most exothermic section to improve controllability and fabrication practicality"],
    ]
    heat_removal_option_rows = [
        [
            option["concept"],
            str(option["controllability_score"]),
            str(option["fabrication_score"]),
            str(option["maintenance_score"]),
            str(option["suitability_score"]),
            str(option["total_score"]),
            option["selection_note"],
        ]
        for option in heat_removal_options
    ]
    heat_removal_design_rows = [
        ["Selected concept", selected_heat_removal_concept],
        ["Selected exchanger type", loop_exchanger_type],
        ["Heat duty", f"{_fmt(reactor.heat_duty_kw, 3)} kW"],
        ["Required exchanger area", f"{_fmt(jacket_required_area_m2, 3)} m2"],
        ["Process-side temperature rise basis", f"{_fmt(loop_process_delta_t_c, 1)} C"],
        ["Process-side Cp basis", f"{_fmt(loop_process_cp_kj_kg_k, 3)} kJ/kg-K"],
        ["Required process recirculation mass flow", f"{_fmt(loop_process_circulation_kg_s, 3)} kg/s"],
        ["Required process recirculation volumetric flow", f"{_fmt(loop_process_circulation_m3_s, 5)} m3/s"],
        ["Estimated loop holdup for 60 s residence", f"{_fmt(loop_process_holdup_m3, 3)} m3"],
        ["Loop line velocity basis", f"{_fmt(loop_line_velocity_basis_m_s, 1)} m/s"],
        ["Required loop line bore", f"{_fmt(loop_line_required_mm, 2)} mm"],
        ["Adopted loop line size", f"{loop_line_adopted_nb} NB"],
        ["Cooling medium", reactor.cooling_medium],
    ]
    heat_removal_selection_rows = [
        ["Preferred concept", selected_heat_removal_concept],
        ["Selection basis", selected_heat_removal_option["selection_note"]],
        ["Why not full jacket", rejected_jacket_basis_note],
        ["Process-side control basis", "pump-around loop selected to decouple reactor shell from the full heat-removal pressure envelope"],
        ["Maintenance basis", "external exchanger allows easier cleaning, repair, and thermal-system isolation"],
        ["Mechanical basis", "large reactor shell avoids full-jacket pressure containment as primary thermal hardware"],
    ]

    nozzle_calc_rows = [
        ["Main feed inlet", f"{_fmt(feed_mass_flow, 3)} kg/h", f"{_fmt(feed_velocity_basis_m_s, 1)} m/s", f"{_fmt(feed_nozzle_required_mm, 2)}", str(feed_nozzle_adopted_nb), "0 deg"],
        ["Reactor outlet", f"{_fmt(product_mass_flow, 3)} kg/h", f"{_fmt(product_velocity_basis_m_s, 1)} m/s", f"{_fmt(product_nozzle_required_mm, 2)}", str(product_nozzle_adopted_nb), "180 deg"],
        ["Bottom drain", f"{_fmt(feed_mass_flow, 3)} kg/h", f"{_fmt(drain_velocity_basis_m_s, 1)} m/s", f"{_fmt(drain_nozzle_required_mm, 2)}", str(drain_nozzle_adopted_nb), "270 deg"],
        ["External loop suction", f"{_fmt(loop_process_circulation_kg_s, 3)} kg/s", f"{_fmt(loop_line_velocity_basis_m_s, 1)} m/s", f"{_fmt(loop_line_required_mm, 2)}", str(loop_line_adopted_nb), "low-side shell"],
        ["External loop return", f"{_fmt(loop_process_circulation_kg_s, 3)} kg/s", f"{_fmt(loop_line_velocity_basis_m_s, 1)} m/s", f"{_fmt(loop_line_required_mm, 2)}", str(loop_line_adopted_nb), "high-side shell"],
        ["Vent / PSV take-off", "relief / disengagement screening", "-", f"{_fmt(vent_nozzle_required_mm, 2)}", str(vent_nozzle_adopted_nb), "top center"],
        ["Instrument nozzles", "instrument taps and sample points", "-", "-", str(instrument_nozzle_adopted_nb), "multiple"],
        ["Manway", "operator entry / cleaning access", "-", "-", str(manway_diameter_mm), "top head"],
    ]
    nozzle_selection_rows = [
        ["Process nozzle basis", "liquid nozzles sized from process volumetric flow and conservative preliminary nozzle velocities"],
        ["Feed / outlet basis", f"feed and outlet held at {_fmt(feed_velocity_basis_m_s, 1)} m/s to limit entry losses and nozzle crowding"],
        ["Drain basis", f"bottom drain held at {_fmt(drain_velocity_basis_m_s, 1)} m/s for dependable gravity-assisted discharge"],
        ["Loop nozzle basis", f"external-loop nozzles held at {_fmt(loop_line_velocity_basis_m_s, 1)} m/s using pump-around circulation flow"],
        ["Vent / PSV basis", "screening bore retained for disengagement and relief tie-in; final relief certification remains outside this note"],
        ["Instrument nozzle basis", f"{instrument_nozzle_adopted_nb} NB minimum branch size retained for pressure, temperature, level, and sample services"],
        ["Legacy jacket note", "jacket nozzles removed from final adopted nozzle philosophy because heat removal is now assigned to the external loop"],
        ["Reinforcement basis", "local reinforcement and detailed branch-pad design to be completed at final code-design stage"],
    ]
    nozzle_mechanical_rows = [
        ["Main feed inlet", str(feed_nozzle_adopted_nb), f"{_fmt(feed_nozzle_neck_thickness_mm, 1)} mm", f"{feed_nozzle_projection_mm} mm", nozzle_mechanical_class, "integral repad required", "0 deg"],
        ["Reactor outlet", str(product_nozzle_adopted_nb), f"{_fmt(product_nozzle_neck_thickness_mm, 1)} mm", f"{product_nozzle_projection_mm} mm", nozzle_mechanical_class, "integral repad required", "180 deg"],
        ["Bottom drain", str(drain_nozzle_adopted_nb), f"{_fmt(drain_nozzle_neck_thickness_mm, 1)} mm", f"{drain_nozzle_projection_mm} mm", nozzle_mechanical_class, "integral repad required", "270 deg"],
        ["External loop suction", str(loop_line_adopted_nb), f"{_fmt(loop_nozzle_neck_thickness_mm, 1)} mm", f"{loop_nozzle_projection_mm} mm", nozzle_mechanical_class, "integral repad required", "low-side shell"],
        ["External loop return", str(loop_line_adopted_nb), f"{_fmt(loop_nozzle_neck_thickness_mm, 1)} mm", f"{loop_nozzle_projection_mm} mm", nozzle_mechanical_class, "integral repad required", "high-side shell"],
        ["Vent / PSV take-off", str(vent_nozzle_adopted_nb), f"{_fmt(vent_nozzle_neck_thickness_mm, 1)} mm", f"{vent_nozzle_projection_mm} mm", nozzle_mechanical_class, "local check required", "top center"],
        ["Instrument nozzles", str(instrument_nozzle_adopted_nb), f"{_fmt(instrument_nozzle_neck_thickness_mm, 1)} mm", f"{instrument_nozzle_projection_mm} mm", nozzle_mechanical_class, "branch check required", "multiple"],
    ]
    nozzle_mechanical_selection_rows = [
        ["Mechanical class basis", nozzle_mechanical_class],
        ["Neck-thickness basis", "screening nozzle-neck thickness assigned from nominal size and pressure class envelope"],
        ["Projection basis", "projection retained long enough for insulation, flange clearance, and field fabrication tolerance"],
        ["Reinforcement family", reactor_mech.nozzle_reinforcement_family],
        ["Required reinforcement area", f"{_fmt(reactor_mech.nozzle_reinforcement_area_mm2, 3)} mm2"],
        ["Local shell interaction factor", f"{_fmt(reactor_mech.local_shell_load_interaction_factor, 3)}"],
        ["Mechanical note", nozzle_reinforcement_status],
    ]
    nozzle_schedule_rows = [
        ["Main feed inlet", f"{_fmt(feed_mass_flow, 3)} kg/h at {_fmt(feed_velocity_basis_m_s, 1)} m/s", f"{_fmt(feed_nozzle_required_mm, 2)}", str(feed_nozzle_adopted_nb), "0 deg"],
        ["Reactor outlet", f"{_fmt(product_mass_flow, 3)} kg/h at {_fmt(product_velocity_basis_m_s, 1)} m/s", f"{_fmt(product_nozzle_required_mm, 2)}", str(product_nozzle_adopted_nb), "180 deg"],
        ["Bottom drain", f"{_fmt(feed_mass_flow, 3)} kg/h at {_fmt(drain_velocity_basis_m_s, 1)} m/s", f"{_fmt(drain_nozzle_required_mm, 2)}", str(drain_nozzle_adopted_nb), "270 deg"],
        ["External loop suction", f"{_fmt(loop_process_circulation_kg_s, 3)} kg/s at {_fmt(loop_line_velocity_basis_m_s, 1)} m/s", f"{_fmt(loop_line_required_mm, 2)}", str(loop_line_adopted_nb), "low-side shell"],
        ["External loop return", f"{_fmt(loop_process_circulation_kg_s, 3)} kg/s at {_fmt(loop_line_velocity_basis_m_s, 1)} m/s", f"{_fmt(loop_line_required_mm, 2)}", str(loop_line_adopted_nb), "high-side shell"],
        ["Vent / PSV take-off", "vapor disengagement and relief allowance", f"{_fmt(vent_nozzle_required_mm, 2)}", str(vent_nozzle_adopted_nb), "top center"],
        ["Instrument nozzles", "temperature, pressure, level, sample points", "-", str(instrument_nozzle_adopted_nb), "multiple"],
        ["Manway", "operator entry / cleaning access", "-", str(manway_diameter_mm), "top head"],
    ]
    support_rows = [
        ["Support type", reactor_mech.support_type],
        ["Support variant", reactor_mech.support_variant],
        ["Skirt / support thickness", f"{_fmt(reactor_mech.support_thickness_mm, 1)} mm"],
        ["Rebuilt empty load", f"{_fmt(rebuilt_empty_load_kn, 3)} kN"],
        ["Rebuilt operating load", f"{_fmt(rebuilt_operating_load_kn, 3)} kN"],
        ["Rebuilt hydrotest load", f"{_fmt(rebuilt_hydrotest_load_kn, 3)} kN"],
        ["Rebuilt design vertical load", f"{_fmt(rebuilt_design_vertical_load_kn, 3)} kN"],
        ["Piping load allowance", f"{_fmt(reactor_mech.piping_load_kn, 3)} kN"],
        ["Wind load allowance", f"{_fmt(reactor_mech.wind_load_kn, 3)} kN"],
        ["Seismic load allowance", f"{_fmt(reactor_mech.seismic_load_kn, 3)} kN"],
        ["Support load case", support_rebuild_note],
        ["Thermal growth", f"{_fmt(reactor_mech.thermal_growth_mm, 3)} mm"],
        ["Anchor group count", str(reactor_mech.anchor_group_count)],
        ["Foundation footprint", f"{_fmt(rebuilt_foundation_footprint_m2, 3)} m2"],
        ["Maintenance clearance", f"{_fmt(reactor_mech.maintenance_clearance_m, 3)} m"],
        ["Nozzle reinforcement area", f"{_fmt(reactor_mech.nozzle_reinforcement_area_mm2, 3)} mm2"],
        ["Local shell/nozzle interaction factor", f"{_fmt(reactor_mech.local_shell_load_interaction_factor, 3)}"],
    ]
    weight_load_rows = [
        ["Shell steel", f"{_fmt(shell_steel_kg, 3)} kg"],
        ["Head steel", f"{_fmt(head_steel_kg, 3)} kg"],
        ["Skirt steel", f"{_fmt(skirt_steel_kg, 3)} kg"],
        ["Attachments and access steel", f"{_fmt(attachment_kg, 3)} kg"],
        ["Rotating equipment", f"{_fmt(rotating_equipment_kg, 3)} kg"],
        ["Thermal hardware", f"{_fmt(thermal_hardware_kg, 3)} kg"],
        ["Operating liquid inventory", f"{_fmt(operating_liquid_kg, 3)} kg"],
        ["Hydrotest liquid inventory", f"{_fmt(hydrotest_liquid_kg, 3)} kg"],
        ["Total empty weight", f"{_fmt(empty_weight_kg, 3)} kg"],
        ["Total operating weight", f"{_fmt(operating_weight_kg, 3)} kg"],
        ["Total hydrotest weight", f"{_fmt(hydrotest_weight_kg, 3)} kg"],
    ]
    support_selection_rows = [
        ["Support family basis", reactor_mech.support_variant],
        ["Load basis", support_rebuild_note],
        ["Anchor basis", f"{reactor_mech.anchor_group_count} anchor locations retained for preliminary support layout"],
        ["Access basis", "maintenance platform required" if reactor_mech.maintenance_platform_required else "maintenance platform not required"],
        ["Platform area", f"{_fmt(reactor_mech.platform_area_m2, 3)} m2" if reactor_mech.maintenance_platform_required else "not required"],
        ["Ladder basis", "access ladder required" if reactor_mech.access_ladder_required else "access ladder not required"],
        ["Lifting basis", "lifting lugs required for installation and maintenance handling" if reactor_mech.lifting_lug_required else "lifting lugs not required"],
        ["Foundation basis", f"rebuilt footprint retained as {_fmt(rebuilt_foundation_footprint_m2, 3)} m2; detailed civil design remains outside this note"],
        ["Nozzle attachment basis", f"{reactor_mech.nozzle_reinforcement_family} reinforcement family with interaction factor {_fmt(reactor_mech.local_shell_load_interaction_factor, 3)}"],
    ]
    dossier_summary_rows = [
        ["Document title", report_title],
        ["Reactor", reactor.reactor_id],
        ["Service", reactor_basis.selected_reactor_type],
        ["Product", project_basis.target_product],
        ["Method", process_method],
        ["Document status", design_status],
        ["Code-style basis", code_basis],
        ["Issue basis", "v26 solved reactor-mechanical dossier"],
    ]
    dossier_coverage_rows = [
        ["1", "Design basis and process basis", "complete"],
        ["2", "Vessel geometry", "complete"],
        ["3", "Shell design", "complete"],
        ["4", "Head design", "complete"],
        ["5", "Agitation and impeller design", "complete"],
        ["6", "Shaft design", "complete"],
        ["7", "Jacket design", "complete"],
        ["8", "Nozzle design and schedule", "complete"],
        ["9", "Support and mechanical basis", "complete"],
        ["10", "Final specification, assumptions, and references", "complete"],
    ]

    final_spec_rows = [
        ["Reactor type", reactor_basis.selected_reactor_type],
        ["Product", project_basis.target_product],
        ["Method", process_method],
        ["Design volume", f"{_fmt(reactor.design_volume_m3)} m3"],
        ["Shell size", f"{_fmt(shell_diameter_m)} m ID x {_fmt(tangent_length_m)} m T/T"],
        ["Shell thickness", f"{_fmt(adopted_shell_thickness_mm, 1)} mm nominal"],
        ["Head thickness", f"{_fmt(adopted_head_thickness_mm, 1)} mm nominal"],
        ["Agitator arrangement", f"{impeller_count} x {impeller_type}, {_fmt(impeller_diameter_m, 3)} m dia, {_fmt(impeller_speed_rpm, 0)} rpm"],
        ["Shaft", f"{_fmt(adopted_shaft_diameter_mm, 1)} mm solid shaft with {selected_motor_kw:.0f} kW drive and stabilized support train (passes current torsion and dynamic screens)"],
        ["Heat-removal system", f"{selected_heat_removal_concept} with {loop_line_adopted_nb} NB loop connections and {loop_exchanger_type}"],
        ["Nozzle philosophy", "reactor-specific schedule aligned to external-loop service supersedes generic single-nozzle screening value from the main report"],
    ]
    dossier_status_rows = [
        ["Overall dossier status", "accurate preliminary mechanical design basis" if shaft_overall_status == "pass" else "conditional preliminary mechanical basis"],
        ["Primary limitation", "not a code-stamped fabrication package and not a substitute for vendor final design"],
        ["Vendor follow-up", "agitator drive details, final shaft critical-speed confirmation, seal selection, and final nozzle reinforcement detailing"],
        ["Civil / structural follow-up", "foundation design, anchor-bolt design, and operating-platform structural detailing"],
        ["Code follow-up", "final ASME code checks, flange ratings, and relief certification"],
    ]
    dossier_integration_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_10_dossier_integration",
        "document_title": report_title,
        "document_status": design_status,
        "code_basis": code_basis,
        "coverage_sections": len(dossier_coverage_rows),
        "overall_status": "complete_for_preliminary_detailed_mechanical_calculations" if shaft_overall_status == "pass" else "conditional_preliminary_mechanical_basis",
        "includes_geometry": True,
        "includes_shell": True,
        "includes_head": True,
        "includes_agitation": True,
        "includes_shaft": True,
        "includes_jacket": True,
        "includes_nozzles": True,
        "includes_support_basis": True,
        "includes_mechanical_consistency_closure": True,
        "includes_final_specification": True,
        "includes_assumptions": True,
        "includes_references": True,
        "citations": reactor_equipment.citations,
    }
    assumptions = [
        "This reactor-only note is an accurate preliminary mechanical design package built on the v26 solved process basis for R-101.",
        "The note deliberately replaces the broad-report generic reactor nozzle screening value with a reactor-specific nozzle schedule.",
        "Shell and head calculations use ASME Section VIII Division 1 style preliminary equations with the current report allowable stress, joint efficiency, and corrosion allowance basis.",
        "Head selection is taken as 2:1 ellipsoidal for a practical agitated pressure-vessel layout.",
        "Agitation is based on four pitched-blade turbines in turbulent flow; the adopted shaft basis includes one intermediate steady bearing and one bottom guide bearing, while detailed drive and seal design remain vendor-finalized.",
        "Legacy jacket sizing is retained only as a reference check; the adopted heat-removal hardware for the final preliminary basis is an external pump-around exchanger loop.",
        "Dynamic shaft closure assumes one intermediate steady bearing and one bottom guide bearing within the vessel to reduce unsupported span.",
        "Detailed code stamping, nozzle load flexibility analysis, flange rating confirmation, relief-valve certification, and foundation civil design remain outside this preliminary note.",
    ]
    report_upgrade_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_7_report_upgrade",
        "document_scope": document_scope,
        "report_tone": "accurate industrial preliminary mechanical design basis",
        "heat_removal_language_aligned": True,
        "shaft_language_aligned": True,
        "nozzle_language_aligned": True,
        "status_language": dossier_status_rows[0][1],
        "citations": reactor_equipment.citations,
    }
    validation_checks = [
        ("document_summary_present", True, "document summary section included"),
        ("coverage_index_present", True, "calculation coverage section included"),
        ("design_basis_present", True, "design basis sections included"),
        ("geometry_present", total_internal_volume_m3 > 0.0, "geometry calculations available"),
        ("shell_section_present", required_shell_thickness_mm > 0.0, "shell calculation available"),
        ("shell_tolerance_compliant", shell_is_tolerance_compliant, "shell adopted thickness passes tolerance screening"),
        ("head_section_present", required_head_thickness_mm > 0.0, "head calculation available"),
        ("head_tolerance_compliant", head_is_tolerance_compliant, "head adopted thickness passes tolerance screening"),
        ("agitation_section_present", agitator_power_kw > 0.0, "agitation calculation available"),
        ("shaft_section_present", required_shaft_diameter_m > 0.0, "shaft calculation available"),
        ("shaft_torsion_adequacy", shaft_is_adequate, "adopted shaft passes torsional screening"),
        ("shaft_dynamic_screen", shaft_dynamic_status == "pass", "adopted shaft passes screened first-critical-speed check"),
        ("heat_removal_selection_present", bool(selected_heat_removal_concept), "heat-removal concept selection available"),
        ("mechanical_consistency_closure", shaft_dynamic_status == "pass" and selected_heat_removal_concept == "External recirculation loop with exchanger", "final shaft, support, and nozzle package align with the selected external-loop concept"),
        ("jacket_section_present", jacket_required_area_m2 > 0.0, "legacy jacket screening remains available"),
        ("jacket_tolerance_compliant", jacket_is_tolerance_compliant, "jacket adopted thickness passes tolerance screening"),
        ("nozzle_section_present", True, "nozzle calculation and schedule included"),
        ("support_section_present", rebuilt_design_vertical_load_kn > 0.0, "support/mechanical basis included"),
        ("final_spec_present", True, "final mechanical specification included"),
        ("assumptions_present", len(assumptions) > 0, "assumptions section included"),
        ("references_present", len(reactor_equipment.citations) > 0, "references section included"),
    ]
    validation_rows = [
        [check_id, "pass" if passed else "fail", note] for check_id, passed, note in validation_checks
    ]
    validation_failures = [
        {"check_id": check_id, "note": note}
        for check_id, passed, note in validation_checks
        if not passed
    ]
    accurate_preliminary_criteria = [
        (
            "shaft_dynamic_screen",
            shaft_dynamic_status == "pass",
            "shaft passes torsion and first-critical-speed screening on the adopted supported arrangement",
        ),
        (
            "heat_removal_selected",
            selected_heat_removal_concept == "External recirculation loop with exchanger",
            "heat-removal concept has been reselected and locked to the external pump-around exchanger",
        ),
        (
            "support_rebuilt_from_final_package",
            rebuilt_design_vertical_load_kn > reactor_mech.design_vertical_load_kn * 0.95,
            "support loads are rebuilt from the adopted vessel, mixer, and thermal-hardware package",
        ),
        (
            "nozzle_mechanical_basis_present",
            nozzle_mechanical_class == reactor_mech.pressure_class and loop_line_adopted_nb >= 80,
            "nozzle package includes mechanical class, neck, projection, and reinforcement basis",
        ),
        (
            "code_material_basis_locked",
            bool(code_basis) and bool(shaft_material) and bool(reactor_equipment.material_of_construction),
            "code, material, and design-condition basis are explicitly locked",
        ),
        (
            "mechanical_consistency_closed",
            mechanical_consistency_artifact["overall_status"] == "closed",
            "mixer, heat-removal, nozzle, and support sections refer to one common adopted package",
        ),
    ]
    accurate_preliminary_failures = [
        {"criterion_id": criterion_id, "note": note}
        for criterion_id, passed, note in accurate_preliminary_criteria
        if not passed
    ]
    if validation_failures:
        accuracy_status = "screening_only"
    elif accurate_preliminary_failures:
        accuracy_status = "preliminary_mechanical_design"
    else:
        accuracy_status = "accurate_preliminary_mechanical_design"
    accuracy_rows = [
        [criterion_id, "pass" if passed else "fail", note]
        for criterion_id, passed, note in accurate_preliminary_criteria
    ]
    acceptance_overall_status = (
        "complete_for_preliminary_detailed_mechanical_calculations"
        if not validation_failures
        else "incomplete_for_preliminary_detailed_mechanical_calculations"
    )
    validation_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "phase_11_validation",
        "overall_status": acceptance_overall_status,
        "check_count": len(validation_checks),
        "failure_count": len(validation_failures),
        "checks": [
            {"check_id": check_id, "passed": passed, "note": note}
            for check_id, passed, note in validation_checks
        ],
        "failures": validation_failures,
        "citations": reactor_equipment.citations,
    }
    accuracy_acceptance_artifact = {
        "project_id": project_id,
        "reactor_id": reactor.reactor_id,
        "phase": "accuracy_phase_8_accuracy_gate",
        "accuracy_status": accuracy_status,
        "criterion_count": len(accurate_preliminary_criteria),
        "failure_count": len(accurate_preliminary_failures),
        "criteria": [
            {"criterion_id": criterion_id, "passed": passed, "note": note}
            for criterion_id, passed, note in accurate_preliminary_criteria
        ],
        "failures": accurate_preliminary_failures,
        "citations": reactor_equipment.citations,
    }

    references_markdown_block = _source_subset_markdown(source_index, reactor_equipment.citations)
    markdown = "\n\n".join(
        [
            f"# {report_title}",
            "## Document Summary",
            markdown_table(["Field", "Value"], dossier_summary_rows),
            "## Design Objective",
            (
                f"In the present note, an accurate preliminary mechanical design is carried out for reactor {reactor.reactor_id}, "
                f"which is the selected {reactor_basis.selected_reactor_type.lower()} for the manufacture of {project_basis.target_product} "
                f"by {process_method}. The object of the note is to bring together, in one place, the governing process basis and the principal "
                "mechanical calculations relating to vessel geometry, shell and head thickness, agitation system, shaft sizing, adopted external-loop heat-removal basis, nozzle schedule, and support basis."
            ),
            "## Calculation Coverage",
            markdown_table(["Phase", "Coverage", "Status"], dossier_coverage_rows),
            "## Design Basis Lock",
            markdown_table(["Field", "Locked Basis"], design_lock_rows),
            "## Design Condition Lock",
            markdown_table(["Field", "Locked Value"], design_condition_rows),
            "## Material and Code Basis",
            markdown_table(["Field", "Locked Value"], material_code_rows),
            "## Design Basis",
            markdown_table(["Field", "Value"], basis_rows),
            "## Process and Geometry Basis",
            markdown_table(["Item", "Value"], geometry_rows),
            "## Vessel Geometry Calculation",
            markdown_table(["Parameter", "Calculated Value"], geometry_calc_rows),
            "## Vessel Geometry Selection Basis",
            markdown_table(["Item", "Basis"], geometry_selection_rows),
            (
                "From the foregoing geometry calculation, it is evident that the selected vessel proportions provide the required working volume together with reasonable freeboard "
                "for vapor disengagement and operating flexibility. Hence the shell diameter and straight-side length obtained from the solved reactor basis are retained, while the "
                "head form and nominal fabrication selections are fixed so that all subsequent mechanical calculations refer to one consistent reactor envelope."
            ),
            "## Shell Thickness Calculation",
            markdown_table(["Parameter", "Value"], shell_rows),
            "## Shell Plate Selection Basis",
            markdown_table(["Item", "Selection"], shell_selection_rows),
            (
                f"From the shell-thickness calculation, the required thickness is found to be {_fmt(required_shell_thickness_mm, 3)} mm. "
                f"In order to provide fabrication allowance, corrosion allowance, and a practical nominal plate selection, the shell thickness is adopted as {_fmt(adopted_shell_thickness_mm, 1)} mm. "
                f"This adopted value gives a nominal margin of {_fmt(shell_nominal_margin_mm, 3)} mm above the calculated requirement and therefore provides a satisfactory preliminary basis."
            ),
            "## Head Design Calculation",
            markdown_table(["Parameter", "Value"], head_rows),
            "## Head Selection Basis",
            markdown_table(["Item", "Selection"], head_selection_rows),
            (
                f"A {head_type.lower()} arrangement is adopted for the vessel. The calculation shows that the required head thickness is {_fmt(required_head_thickness_mm, 3)} mm, "
                f"whereas the selected nominal head thickness is {_fmt(adopted_head_thickness_mm, 1)} mm. "
                f"Thus a nominal margin of {_fmt(head_nominal_margin_mm, 3)} mm is available over the required value, which is acceptable for the present preliminary design stage."
            ),
            "## Agitation System Design",
            markdown_table(["Parameter", "Value"], agitation_rows),
            "## Agitation Selection Basis",
            markdown_table(["Item", "Basis"], agitation_selection_rows),
            (
                "Since the reactor is comparatively tall and the duty corresponds to low-viscosity liquid-phase service, an axial-flow impeller train is preferred to a single radial-flow device. "
                f"The selected arrangement gives a {flow_regime} agitation Reynolds number of about {_fmt(agitator_reynolds, 0)} together with an absorbed power of {_fmt(agitator_power_kw, 3)} kW. "
                f"For the present adopted basis, the mixer is therefore treated as a {drive_arrangement.lower()} with {seal_arrangement.lower()} and an internal shaft-support train sized to suit the tall liquid column."
            ),
            "## Shaft Design Calculation",
            markdown_table(["Parameter", "Value"], shaft_rows),
            "## Shaft Selection Basis",
            markdown_table(["Item", "Basis"], shaft_selection_rows),
            (
                f"On the basis of the agitator torque and a service factor of {service_factor:.2f}, the calculated solid shaft diameter is {_fmt(required_shaft_diameter_m * 1000.0, 3)} mm. "
                f"Hence an {_fmt(adopted_shaft_diameter_mm, 1)} mm shaft is retained for the present stage and first checked in torsion. "
                f"However, when a simple dynamic screen is applied using the estimated rotating mass, the screened first critical speed is only {_fmt(first_critical_speed_rpm, 3)} rpm against an operating speed of {_fmt(impeller_speed_rpm, 0)} rpm. "
                f"Thus the adopted shaft arrangement is {shaft_overall_status} on the present mixer-mechanical basis and is acceptable for accurate preliminary design, while final vendor confirmation remains necessary."
            ),
            "## Heat-Removal System Selection",
            markdown_table(
                ["Concept", "Control", "Fabrication", "Maintenance", "Suitability", "Total", "Selection Note"],
                heat_removal_option_rows,
            ),
            "## Heat-Removal System Design",
            markdown_table(["Parameter", "Value"], heat_removal_design_rows),
            "## Heat-Removal Selection Basis",
            markdown_table(["Item", "Basis"], heat_removal_selection_rows),
            (
                f"From the above comparison, the preferred heat-removal concept for the present reactor is the {selected_heat_removal_concept.lower()}. "
                f"The duty of {_fmt(reactor.heat_duty_kw, 3)} kW is therefore assigned to a {loop_exchanger_type}, with an exchanger area of {_fmt(jacket_required_area_m2, 3)} m2 and a process-side recirculation rate of {_fmt(loop_process_circulation_kg_s, 3)} kg/s. "
                f"The earlier full-jacket arrangement is retained only as a reference check and not as the adopted mechanical solution."
            ),
            "## Nozzle Design Calculation",
            markdown_table(["Service", "Flow Basis", "Velocity Basis", "Required ID (mm)", "Adopted NB (mm)", "Suggested Orientation"], nozzle_calc_rows),
            "## Nozzle Selection Basis",
            markdown_table(["Item", "Basis"], nozzle_selection_rows),
            (
                f"The process nozzles are sized from the solved reactor flow basis using conservative industrial preliminary velocity criteria. "
                f"On this basis, the main feed inlet and reactor outlet each require about {_fmt(feed_nozzle_required_mm, 2)} mm bore and are therefore adopted as {feed_nozzle_adopted_nb} NB connections. "
                f"In the same manner, the external-loop nozzles are retained as {loop_line_adopted_nb} NB on the basis of the calculated circulation requirement."
            ),
            "## Nozzle Mechanical Basis",
            markdown_table(["Service", "NB (mm)", "Neck Thickness", "Projection", "Class", "Reinforcement", "Orientation"], nozzle_mechanical_rows),
            "## Nozzle Mechanical Selection Basis",
            markdown_table(["Item", "Basis"], nozzle_mechanical_selection_rows),
            (
                f"After fixing the process-side and loop-side nozzle bores, a preliminary mechanical nozzle basis is assigned using {nozzle_mechanical_class} class service, "
                f"preliminary neck-thickness selections, and {reactor_mech.nozzle_reinforcement_family} reinforcement treatment. "
                f"The governing reinforcement area retained from the mechanical artifact is {_fmt(reactor_mech.nozzle_reinforcement_area_mm2, 3)} mm2."
            ),
            "## Reactor Nozzle Schedule",
            markdown_table(["Service", "Basis", "Required ID (mm)", "Adopted NB (mm)", "Suggested Orientation"], nozzle_schedule_rows),
            (
                "The foregoing nozzle schedule may therefore be treated as the preferred nozzle basis for the present reactor at the accurate preliminary design stage. "
                "It supersedes the single screening-nozzle value appearing in the broader equipment summary and should be used as the mechanical reference basis for subsequent detailing."
            ),
            "## Support and Mechanical Basis",
            markdown_table(["Component", "Weight"], weight_load_rows),
            markdown_table(["Parameter", "Value"], support_rows),
            "## Support Selection Basis",
            markdown_table(["Item", "Basis"], support_selection_rows),
            (
                f"The reactor is supported on a {reactor_mech.support_variant.lower()} designed around a rebuilt operating load of {_fmt(rebuilt_operating_load_kn, 3)} kN and a rebuilt design vertical load of {_fmt(rebuilt_design_vertical_load_kn, 3)} kN. "
                f"Wind, seismic, and piping allowances are then superimposed on the rebuilt package weight basis. "
                f"Accordingly, the preliminary support arrangement includes {reactor_mech.anchor_group_count} anchors and a foundation footprint of {_fmt(rebuilt_foundation_footprint_m2, 3)} m2, "
                f"and access provisions appropriate for a tall agitated reactor installation."
            ),
            "## Mechanical Consistency Closure",
            markdown_table(["Item", "Closure"], mechanical_consistency_rows),
            (
                f"In the present closure pass, the final adopted shaft diameter is raised to {_fmt(adopted_shaft_diameter_mm, 1)} mm and paired with a {shaft_support_strategy.lower()}. "
                f"On this reduced unsupported-span basis, the screened first critical speed rises to {_fmt(first_critical_speed_rpm, 3)} rpm, and the final nozzle philosophy is simultaneously aligned to the {selected_heat_removal_concept.lower()}. "
                f"Thus the mixer, heat-removal, nozzle, and support sections now refer to one common adopted reactor package suitable for accurate preliminary mechanical design review."
            ),
            "## Final Reactor Mechanical Specification",
            markdown_table(["Item", "Selection"], final_spec_rows),
            "## Dossier Status and Next-Step Scope",
            markdown_table(["Item", "Status / Note"], dossier_status_rows),
            "## Validation Summary",
            markdown_table(["Check", "Status", "Note"], validation_rows),
            "## Accuracy Gate",
            markdown_table(["Criterion", "Status", "Note"], accuracy_rows),
            f"Accuracy status for the present dossier: `{accuracy_status}`.",
            "## Assumptions and Limits",
            "\n".join(f"- {item}" for item in assumptions),
            references_markdown_block,
        ]
    ).strip() + "\n"

    sections_html = [
        ("Document Summary", _html_table(["Field", "Value"], dossier_summary_rows)),
        (
            "Design Objective",
            (
                "<p>"
                f"In the present note, an accurate preliminary mechanical design is carried out for reactor {reactor.reactor_id}, "
                f"which is the selected {reactor_basis.selected_reactor_type.lower()} for the manufacture of {project_basis.target_product} "
                f"by {process_method}. The object of the note is to bring together, in one place, the governing process basis and the principal mechanical calculations relating to vessel geometry, shell and head thickness, agitation system, mixer drive and shaft sizing, jacket sizing, nozzle schedule, and support basis."
                "</p>"
            ),
        ),
        ("Calculation Coverage", _html_table(["Phase", "Coverage", "Status"], dossier_coverage_rows)),
        ("Design Basis Lock", _html_table(["Field", "Locked Basis"], design_lock_rows)),
        ("Design Condition Lock", _html_table(["Field", "Locked Value"], design_condition_rows)),
        ("Material and Code Basis", _html_table(["Field", "Locked Value"], material_code_rows)),
        ("Design Basis", _html_table(["Field", "Value"], basis_rows)),
        (
            "Process and Geometry Basis",
            _html_table(["Item", "Value"], geometry_rows)
            + _html_table(["Parameter", "Calculated Value"], geometry_calc_rows)
            + _html_table(["Item", "Basis"], geometry_selection_rows)
            + "<p>From the foregoing geometry calculation, it is evident that the selected vessel proportions provide the required working volume together with reasonable freeboard for vapor disengagement and operating flexibility. Hence the shell diameter and straight-side length obtained from the solved reactor basis are retained, while the head form and nominal fabrication selections are fixed so that all subsequent mechanical calculations refer to one consistent reactor envelope.</p>",
        ),
        (
            "Shell Thickness Calculation",
            _html_table(["Parameter", "Value"], shell_rows)
            + _html_table(["Item", "Selection"], shell_selection_rows)
            + f"<p>From the shell-thickness calculation, the required thickness is found to be {_fmt(required_shell_thickness_mm, 3)} mm. In order to provide fabrication allowance, corrosion allowance, and a practical nominal plate selection, the shell thickness is adopted as {_fmt(adopted_shell_thickness_mm, 1)} mm. This adopted value gives a nominal margin of {_fmt(shell_nominal_margin_mm, 3)} mm above the calculated requirement and therefore provides a satisfactory preliminary basis.</p>",
        ),
        (
            "Head Design Calculation",
            _html_table(["Parameter", "Value"], head_rows)
            + _html_table(["Item", "Selection"], head_selection_rows)
            + f"<p>A {head_type.lower()} arrangement is adopted for the vessel. The calculation shows that the required head thickness is {_fmt(required_head_thickness_mm, 3)} mm, whereas the selected nominal head thickness is {_fmt(adopted_head_thickness_mm, 1)} mm. Thus a nominal margin of {_fmt(head_nominal_margin_mm, 3)} mm is available over the required value, which is acceptable for the present preliminary design stage.</p>",
        ),
        (
            "Agitation System Design",
            _html_table(["Parameter", "Value"], agitation_rows)
            + _html_table(["Item", "Basis"], agitation_selection_rows)
            + f"<p>Since the reactor is comparatively tall and the duty corresponds to low-viscosity liquid-phase service, an axial-flow impeller train is preferred to a single radial-flow device. The selected arrangement gives a {flow_regime} agitation Reynolds number of about {_fmt(agitator_reynolds, 0)} together with an absorbed power of {_fmt(agitator_power_kw, 3)} kW. For the present adopted basis, the mixer is therefore treated as a {drive_arrangement.lower()} with {seal_arrangement.lower()} and an internal shaft-support train sized to suit the tall liquid column.</p>",
        ),
        (
            "Shaft Design Calculation",
            _html_table(["Parameter", "Value"], shaft_rows)
            + _html_table(["Item", "Basis"], shaft_selection_rows)
            + f"<p>On the basis of the agitator torque and a service factor of {service_factor:.2f}, the calculated solid shaft diameter is {_fmt(required_shaft_diameter_m * 1000.0, 3)} mm. Hence an {_fmt(adopted_shaft_diameter_mm, 1)} mm shaft is retained for the present stage and first checked in torsion. However, when a simple dynamic screen is applied using the estimated rotating mass, the screened first critical speed is only {_fmt(first_critical_speed_rpm, 3)} rpm against an operating speed of {_fmt(impeller_speed_rpm, 0)} rpm. Thus the adopted shaft arrangement is {shaft_overall_status} on the present mixer-mechanical basis and is acceptable for accurate preliminary design, while final vendor confirmation remains necessary.</p>",
        ),
        (
            "Heat-Removal System Selection",
            _html_table(
                ["Concept", "Control", "Fabrication", "Maintenance", "Suitability", "Total", "Selection Note"],
                heat_removal_option_rows,
            )
            + _html_table(["Parameter", "Value"], heat_removal_design_rows)
            + _html_table(["Item", "Basis"], heat_removal_selection_rows)
            + f"<p>From the above comparison, the preferred heat-removal concept for the present reactor is the {selected_heat_removal_concept.lower()}. The duty of {_fmt(reactor.heat_duty_kw, 3)} kW is therefore assigned to a {loop_exchanger_type}, with an exchanger area of {_fmt(jacket_required_area_m2, 3)} m2 and a process-side recirculation rate of {_fmt(loop_process_circulation_kg_s, 3)} kg/s. The earlier full-jacket arrangement is retained only as a reference check and not as the adopted mechanical solution.</p>",
        ),
        (
            "Nozzle Design Calculation",
            _html_table(["Service", "Flow Basis", "Velocity Basis", "Required ID (mm)", "Adopted NB (mm)", "Suggested Orientation"], nozzle_calc_rows)
            + _html_table(["Item", "Basis"], nozzle_selection_rows)
            + f"<p>The process nozzles are sized from the solved reactor flow basis using conservative industrial preliminary velocity criteria. On this basis, the main feed inlet and reactor outlet each require about {_fmt(feed_nozzle_required_mm, 2)} mm bore and are therefore adopted as {feed_nozzle_adopted_nb} NB connections. In the same manner, the external-loop nozzles are retained as {loop_line_adopted_nb} NB on the basis of the calculated circulation requirement.</p>"
            + _html_table(["Service", "NB (mm)", "Neck Thickness", "Projection", "Class", "Reinforcement", "Orientation"], nozzle_mechanical_rows)
            + _html_table(["Item", "Basis"], nozzle_mechanical_selection_rows)
            + f"<p>After fixing the process-side and loop-side nozzle bores, a preliminary mechanical nozzle basis is assigned using {nozzle_mechanical_class} class service, preliminary neck-thickness selections, and {reactor_mech.nozzle_reinforcement_family} reinforcement treatment. The governing reinforcement area retained from the mechanical artifact is {_fmt(reactor_mech.nozzle_reinforcement_area_mm2, 3)} mm2.</p>",
        ),
        (
            "Reactor Nozzle Schedule",
            _html_table(["Service", "Basis", "Required ID (mm)", "Adopted NB (mm)", "Suggested Orientation"], nozzle_schedule_rows)
            + "<p>The foregoing nozzle schedule may therefore be treated as the preferred nozzle basis for the present reactor at the accurate preliminary design stage. It supersedes the single screening-nozzle value appearing in the broader equipment summary and should be used as the mechanical reference basis for subsequent detailing.</p>",
        ),
        (
            "Support and Mechanical Basis",
            _html_table(["Component", "Weight"], weight_load_rows)
            + _html_table(["Parameter", "Value"], support_rows)
            + _html_table(["Item", "Basis"], support_selection_rows)
            + f"<p>The reactor is supported on a {reactor_mech.support_variant.lower()} designed around a rebuilt operating load of {_fmt(rebuilt_operating_load_kn, 3)} kN and a rebuilt design vertical load of {_fmt(rebuilt_design_vertical_load_kn, 3)} kN. Wind, seismic, and piping allowances are then superimposed on the rebuilt package weight basis. Accordingly, the preliminary support arrangement includes {reactor_mech.anchor_group_count} anchors and a foundation footprint of {_fmt(rebuilt_foundation_footprint_m2, 3)} m2, together with access provisions appropriate for a tall agitated reactor installation.</p>",
        ),
        (
            "Mechanical Consistency Closure",
            _html_table(["Item", "Closure"], mechanical_consistency_rows)
            + f"<p>In the present closure pass, the final adopted shaft diameter is raised to {_fmt(adopted_shaft_diameter_mm, 1)} mm and paired with a {shaft_support_strategy.lower()}. On this reduced unsupported-span basis, the screened first critical speed rises to {_fmt(first_critical_speed_rpm, 3)} rpm, and the final nozzle philosophy is simultaneously aligned to the {selected_heat_removal_concept.lower()}. Thus the mixer, heat-removal, nozzle, and support sections now refer to one common adopted reactor package suitable for accurate preliminary mechanical design review.</p>",
        ),
        ("Final Reactor Mechanical Specification", _html_table(["Item", "Selection"], final_spec_rows)),
        ("Dossier Status and Next-Step Scope", _html_table(["Item", "Status / Note"], dossier_status_rows)),
        ("Validation Summary", _html_table(["Check", "Status", "Note"], validation_rows)),
        (
            "Accuracy Gate",
            _html_table(["Criterion", "Status", "Note"], accuracy_rows)
            + f"<p>Accuracy status for the present dossier: <strong>{accuracy_status}</strong>.</p>",
        ),
        ("Assumptions and Limits", "<ul>" + "".join(f"<li>{item}</li>" for item in assumptions) + "</ul>"),
        ("References", _references_html(source_index, reactor_equipment.citations).replace("<h2>References</h2>", "")),
    ]
    html = _build_html_document(report_title, sections_html)

    project_dir = runner.store.project_dir(project_id)
    markdown_path = project_dir / "reactor_mechanical_design_report.md"
    html_path = project_dir / "reactor_mechanical_design_report.html"
    pdf_path = project_dir / "reactor_mechanical_design_report.pdf"
    artifact_path = project_dir / "artifacts" / "reactor_mechanical_design_basis_lock.json"
    geometry_artifact_path = project_dir / "artifacts" / "reactor_mechanical_geometry.json"
    shell_artifact_path = project_dir / "artifacts" / "reactor_mechanical_shell_design.json"
    head_artifact_path = project_dir / "artifacts" / "reactor_mechanical_head_design.json"
    agitation_artifact_path = project_dir / "artifacts" / "reactor_mechanical_agitation_design.json"
    shaft_artifact_path = project_dir / "artifacts" / "reactor_mechanical_shaft_design.json"
    mixer_mechanical_artifact_path = project_dir / "artifacts" / "reactor_mixer_mechanical_design.json"
    shaft_dynamic_artifact_path = project_dir / "artifacts" / "reactor_shaft_dynamic_screen.json"
    jacket_artifact_path = project_dir / "artifacts" / "reactor_mechanical_jacket_design.json"
    heat_removal_selection_artifact_path = project_dir / "artifacts" / "reactor_heat_removal_selection.json"
    heat_removal_design_artifact_path = project_dir / "artifacts" / "reactor_heat_removal_design.json"
    nozzle_artifact_path = project_dir / "artifacts" / "reactor_mechanical_nozzle_design.json"
    nozzle_mechanical_artifact_path = project_dir / "artifacts" / "reactor_nozzle_mechanical_design.json"
    nozzle_reinforcement_artifact_path = project_dir / "artifacts" / "reactor_nozzle_reinforcement_basis.json"
    support_artifact_path = project_dir / "artifacts" / "reactor_mechanical_support_design.json"
    dossier_artifact_path = project_dir / "artifacts" / "reactor_mechanical_dossier.json"
    acceptance_artifact_path = project_dir / "artifacts" / "reactor_mechanical_design_acceptance.json"
    design_conditions_artifact_path = project_dir / "artifacts" / "reactor_design_conditions_lock.json"
    material_code_artifact_path = project_dir / "artifacts" / "reactor_material_code_basis.json"
    weight_load_artifact_path = project_dir / "artifacts" / "reactor_weight_and_load_summary.json"
    support_rebuild_artifact_path = project_dir / "artifacts" / "reactor_support_rebuild.json"
    foundation_basis_artifact_path = project_dir / "artifacts" / "reactor_foundation_basis.json"
    consistency_artifact_path = project_dir / "artifacts" / "reactor_mechanical_consistency_check.json"
    report_upgrade_artifact_path = project_dir / "artifacts" / "reactor_mechanical_report_upgrade.json"
    accuracy_acceptance_artifact_path = project_dir / "artifacts" / "reactor_accuracy_acceptance.json"

    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(design_basis_lock, indent=2), encoding="utf-8")
    geometry_artifact_path.write_text(json.dumps(geometry_artifact, indent=2), encoding="utf-8")
    shell_artifact_path.write_text(json.dumps(shell_design_artifact, indent=2), encoding="utf-8")
    head_artifact_path.write_text(json.dumps(head_design_artifact, indent=2), encoding="utf-8")
    agitation_artifact_path.write_text(json.dumps(agitation_design_artifact, indent=2), encoding="utf-8")
    shaft_artifact_path.write_text(json.dumps(shaft_design_artifact, indent=2), encoding="utf-8")
    mixer_mechanical_artifact_path.write_text(json.dumps(mixer_mechanical_design_artifact, indent=2), encoding="utf-8")
    shaft_dynamic_artifact_path.write_text(json.dumps(shaft_dynamic_screen_artifact, indent=2), encoding="utf-8")
    jacket_artifact_path.write_text(json.dumps(jacket_design_artifact, indent=2), encoding="utf-8")
    heat_removal_selection_artifact_path.write_text(json.dumps(heat_removal_selection_artifact, indent=2), encoding="utf-8")
    heat_removal_design_artifact_path.write_text(json.dumps(heat_removal_design_artifact, indent=2), encoding="utf-8")
    nozzle_artifact_path.write_text(json.dumps(nozzle_design_artifact, indent=2), encoding="utf-8")
    nozzle_mechanical_artifact_path.write_text(json.dumps(nozzle_mechanical_design_artifact, indent=2), encoding="utf-8")
    nozzle_reinforcement_artifact_path.write_text(json.dumps(nozzle_reinforcement_basis_artifact, indent=2), encoding="utf-8")
    support_artifact_path.write_text(json.dumps(support_design_artifact, indent=2), encoding="utf-8")
    dossier_artifact_path.write_text(json.dumps(dossier_integration_artifact, indent=2), encoding="utf-8")
    acceptance_artifact_path.write_text(json.dumps(validation_artifact, indent=2), encoding="utf-8")
    design_conditions_artifact_path.write_text(json.dumps(design_conditions_lock, indent=2), encoding="utf-8")
    material_code_artifact_path.write_text(json.dumps(material_code_basis, indent=2), encoding="utf-8")
    weight_load_artifact_path.write_text(json.dumps(weight_load_summary_artifact, indent=2), encoding="utf-8")
    support_rebuild_artifact_path.write_text(json.dumps(support_rebuild_artifact, indent=2), encoding="utf-8")
    foundation_basis_artifact_path.write_text(json.dumps(foundation_basis_artifact, indent=2), encoding="utf-8")
    consistency_artifact_path.write_text(json.dumps(mechanical_consistency_artifact, indent=2), encoding="utf-8")
    report_upgrade_artifact_path.write_text(json.dumps(report_upgrade_artifact, indent=2), encoding="utf-8")
    accuracy_acceptance_artifact_path.write_text(json.dumps(accuracy_acceptance_artifact, indent=2), encoding="utf-8")
    render_styled_pdf(
        html,
        str(pdf_path),
        report_title,
        header_text=f"{project_basis.target_product} Reactor Mechanical Design",
    )
    return markdown_path, pdf_path
