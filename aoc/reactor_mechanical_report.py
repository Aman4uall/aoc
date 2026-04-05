from __future__ import annotations

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
    adopted_shell_thickness_mm = 8.0
    adopted_head_thickness_mm = 8.0

    impeller_type = "45 degree pitched-blade turbine"
    impeller_count = 4
    impeller_diameter_m = 0.35 * shell_diameter_m
    impeller_speed_rpm = 60.0
    impeller_speed_rps = impeller_speed_rpm / 60.0
    power_number = 1.5
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
    adopted_shaft_diameter_mm = 80.0
    selected_motor_kw = 15.0
    baffle_count = 4
    baffle_width_m = shell_diameter_m / 12.0
    impeller_spacing_m = tangent_length_m / (impeller_count + 1)

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
    jacket_nozzle_required_mm = math.sqrt((4.0 * jacket_flow_m3_s) / (math.pi * 2.0)) * 1000.0
    jacket_nozzle_adopted_nb = _pick_standard_nb(jacket_nozzle_required_mm)
    required_jacket_shell_thickness_mm = (
        ((jacket_design_pressure_bar / 10.0) * jacket_outer_diameter_m * 1000.0)
        / ((2.0 * allowable_stress_mpa * joint_efficiency) - (1.2 * (jacket_design_pressure_bar / 10.0)))
    ) + corrosion_allowance_mm
    adopted_jacket_shell_thickness_mm = 12.0

    process_flow_m3_s = (feed_mass_flow / process_density) / 3600.0
    feed_nozzle_required_mm = math.sqrt((4.0 * process_flow_m3_s) / (math.pi * 1.5)) * 1000.0
    product_nozzle_required_mm = math.sqrt((4.0 * process_flow_m3_s) / (math.pi * 1.5)) * 1000.0
    drain_nozzle_required_mm = math.sqrt((4.0 * process_flow_m3_s) / (math.pi * 1.0)) * 1000.0
    vent_nozzle_required_mm = 10.0

    feed_nozzle_adopted_nb = _pick_standard_nb(feed_nozzle_required_mm)
    product_nozzle_adopted_nb = _pick_standard_nb(product_nozzle_required_mm)
    drain_nozzle_adopted_nb = _pick_standard_nb(drain_nozzle_required_mm)
    vent_nozzle_adopted_nb = _pick_standard_nb(vent_nozzle_required_mm)
    instrument_nozzle_adopted_nb = 25
    manway_diameter_mm = 600

    report_title = (
        f"Detailed Mechanical Design of Reactor {reactor.reactor_id} for "
        f"{project_basis.target_product}"
    )
    process_method = "liquid-phase Menshutkin quaternization of dodecyldimethylamine with benzyl chloride"

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

    shell_rows = [
        ["Equation", "t = P D / (2 S E - 1.2 P) + CA"],
        ["P", f"{_fmt(pressure_mpa, 3)} MPa"],
        ["D", f"{_fmt(shell_diameter_m, 3)} m"],
        ["S", f"{_fmt(allowable_stress_mpa, 1)} MPa"],
        ["E", f"{_fmt(joint_efficiency, 2)}"],
        ["CA", f"{_fmt(corrosion_allowance_mm, 1)} mm"],
        ["Required shell thickness", f"{_fmt(required_shell_thickness_mm, 3)} mm"],
        ["Adopted nominal shell thickness", f"{_fmt(adopted_shell_thickness_mm, 1)} mm"],
    ]

    head_rows = [
        ["Selected head", head_type],
        ["Equation", "t = 0.885 P D / (2 S E - 0.1 P) + CA"],
        ["Required head thickness", f"{_fmt(required_head_thickness_mm, 3)} mm"],
        ["Adopted nominal head thickness", f"{_fmt(adopted_head_thickness_mm, 1)} mm"],
        ["Hydrotest pressure", f"{_fmt(reactor_mech.hydrotest_pressure_bar, 3)} bar"],
    ]

    agitation_rows = [
        ["Impeller type", impeller_type],
        ["Number of impellers", str(impeller_count)],
        ["Impeller diameter", f"{_fmt(impeller_diameter_m, 3)} m"],
        ["Impeller diameter ratio (D/T)", f"{_fmt(impeller_diameter_m / shell_diameter_m, 3)}"],
        ["Rotational speed", f"{_fmt(impeller_speed_rpm, 0)} rpm"],
        ["Tip speed", f"{_fmt(agitator_tip_speed_m_s, 3)} m/s"],
        ["Agitator Reynolds number", f"{_fmt(agitator_reynolds, 0)}"],
        ["Calculated agitator power", f"{_fmt(agitator_power_kw, 3)} kW"],
        ["Selected motor", f"{_fmt(selected_motor_kw, 1)} kW"],
        ["Baffle arrangement", f"{baffle_count} baffles x {_fmt(baffle_width_m, 3)} m width"],
        ["Vertical impeller spacing", f"{_fmt(impeller_spacing_m, 3)} m"],
    ]

    shaft_rows = [
        ["Power transmitted", f"{_fmt(agitator_power_kw, 3)} kW"],
        ["Running torque", f"{_fmt(design_torque_n_m, 3)} N.m"],
        ["Service factor", f"{_fmt(service_factor, 2)}"],
        ["Design torque", f"{_fmt(design_torque_with_factor_n_m, 3)} N.m"],
        ["Allowable shaft shear stress", "35 MPa"],
        ["Required shaft diameter", f"{_fmt(required_shaft_diameter_m * 1000.0, 3)} mm"],
        ["Adopted solid shaft diameter", f"{_fmt(adopted_shaft_diameter_mm, 1)} mm"],
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
        ["Utility flow", f"{_fmt(jacket_flow_kg_s, 3)} kg/s"],
        ["Required jacket shell thickness", f"{_fmt(required_jacket_shell_thickness_mm, 3)} mm"],
        ["Adopted jacket shell thickness", f"{_fmt(adopted_jacket_shell_thickness_mm, 1)} mm"],
    ]

    nozzle_rows = [
        ["Main feed inlet", f"{_fmt(feed_mass_flow, 3)} kg/h at 1.5 m/s", f"{_fmt(feed_nozzle_required_mm, 2)}", str(feed_nozzle_adopted_nb), "0 deg"],
        ["Reactor outlet", f"{_fmt(product_mass_flow, 3)} kg/h at 1.5 m/s", f"{_fmt(product_nozzle_required_mm, 2)}", str(product_nozzle_adopted_nb), "180 deg"],
        ["Bottom drain", f"{_fmt(feed_mass_flow, 3)} kg/h at 1.0 m/s", f"{_fmt(drain_nozzle_required_mm, 2)}", str(drain_nozzle_adopted_nb), "270 deg"],
        ["Jacket inlet", f"{_fmt(jacket_flow_kg_s, 3)} kg/s at 2.0 m/s", f"{_fmt(jacket_nozzle_required_mm, 2)}", str(jacket_nozzle_adopted_nb), "90 deg"],
        ["Jacket outlet", f"{_fmt(jacket_flow_kg_s, 3)} kg/s at 2.0 m/s", f"{_fmt(jacket_nozzle_required_mm, 2)}", str(jacket_nozzle_adopted_nb), "270 deg"],
        ["Vent / PSV take-off", "vapor disengagement and relief allowance", f"{_fmt(vent_nozzle_required_mm, 2)}", str(vent_nozzle_adopted_nb), "top center"],
        ["Instrument nozzles", "temperature, pressure, level, sample points", "-", str(instrument_nozzle_adopted_nb), "multiple"],
        ["Manway", "operator entry / cleaning access", "-", str(manway_diameter_mm), "top head"],
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
        ["Shaft", f"{_fmt(adopted_shaft_diameter_mm, 1)} mm solid shaft with {selected_motor_kw:.0f} kW drive"],
        ["Jacket", f"{_fmt(adopted_jacket_height_m, 3)} m effective jacket zone, {jacket_nozzle_adopted_nb} NB utility nozzles"],
        ["Nozzle philosophy", "reactor-specific schedule supersedes generic single-nozzle screening value from the main report"],
    ]

    assumptions = [
        "This reactor-only note is a preliminary mechanical design package built on the v26 solved process basis for R-101.",
        "The note deliberately replaces the broad-report generic reactor nozzle screening value with a reactor-specific nozzle schedule.",
        "Shell and head calculations use ASME-style screening equations with the current report allowable stress, joint efficiency, and corrosion allowance basis.",
        "Head selection is taken as 2:1 ellipsoidal for a practical agitated pressure-vessel layout.",
        "Agitation is based on four pitched-blade turbines in turbulent flow; motor and shaft selections remain preliminary and should be finalized with vendor data.",
        "Jacket sizing uses the current reactor duty and overall heat-transfer basis, then translates that into a practical sectional jacket arrangement.",
        "Detailed code stamping, nozzle load flexibility analysis, flange rating confirmation, relief-valve certification, and foundation civil design remain outside this preliminary note.",
    ]

    references_markdown_block = _source_subset_markdown(source_index, reactor_equipment.citations)
    markdown = "\n\n".join(
        [
            f"# {report_title}",
            "## Design Objective",
            (
                f"This standalone note presents a focused preliminary mechanical design for reactor {reactor.reactor_id}, "
                f"the selected {reactor_basis.selected_reactor_type.lower()} used for the manufacture of {project_basis.target_product} "
                f"by {process_method}. The purpose of the note is to consolidate the process basis, shell and head sizing, "
                "agitation and shaft selection, jacket sizing, and the inlet/outlet nozzle schedule into one reactor-centered document."
            ),
            "## Design Basis",
            markdown_table(["Field", "Value"], basis_rows),
            "## Process and Geometry Basis",
            markdown_table(["Item", "Value"], geometry_rows),
            (
                "The vessel geometry is tied to the solved v26 reactor basis. The straight-side shell length is kept from the current reactor design packet, "
                "while the head selection and nominal plate choices are rounded to practical fabrication values."
            ),
            "## Shell Thickness Calculation",
            markdown_table(["Parameter", "Value"], shell_rows),
            (
                f"The required shell thickness comes out to {_fmt(required_shell_thickness_mm, 3)} mm. "
                f"For fabrication and corrosion margin, the shell is selected as {_fmt(adopted_shell_thickness_mm, 1)} mm nominal plate."
            ),
            "## Head Design Calculation",
            markdown_table(["Parameter", "Value"], head_rows),
            (
                f"A {head_type.lower()} arrangement is adopted. The calculated head thickness is {_fmt(required_head_thickness_mm, 3)} mm, "
                f"and the selected nominal head thickness is {_fmt(adopted_head_thickness_mm, 1)} mm."
            ),
            "## Agitation System Design",
            markdown_table(["Parameter", "Value"], agitation_rows),
            (
                "Because the reactor is tall and operates in low-viscosity liquid service, multiple axial-flow impellers are more appropriate than a single high-power radial turbine. "
                f"The selected arrangement gives a turbulent agitation Reynolds number of about {_fmt(agitator_reynolds, 0)} and an absorbed agitation power of {_fmt(agitator_power_kw, 3)} kW."
            ),
            "## Shaft Design Calculation",
            markdown_table(["Parameter", "Value"], shaft_rows),
            (
                f"Using the agitator torque with a service factor of {service_factor:.2f}, the calculated solid-shaft diameter is {_fmt(required_shaft_diameter_m * 1000.0, 3)} mm. "
                f"An adopted {_fmt(adopted_shaft_diameter_mm, 1)} mm shaft gives a practical preliminary selection for vendor detailing."
            ),
            "## Jacket Design Calculation",
            markdown_table(["Parameter", "Value"], jacket_rows),
            (
                f"The existing reactor duty requires approximately {_fmt(jacket_required_area_m2, 3)} m2 of effective transfer area. "
                f"On a full-circumference shell basis this corresponds to about {_fmt(jacket_equivalent_height_m, 3)} m of active jacket coverage, "
                f"so the standalone reactor design adopts a {_fmt(adopted_jacket_height_m, 3)} m effective jacketed zone for controllability and fabrication convenience."
            ),
            "## Reactor Nozzle Schedule",
            markdown_table(["Service", "Basis", "Required ID (mm)", "Adopted NB (mm)", "Suggested Orientation"], nozzle_rows),
            (
                "These nozzle sizes are reactor-specific preliminary values derived from actual process and utility flow criteria. "
                "They should be treated as the preferred nozzle schedule for the standalone reactor note, rather than the single global screening nozzle size carried in the broad equipment summary."
            ),
            "## Final Reactor Mechanical Specification",
            markdown_table(["Item", "Selection"], final_spec_rows),
            "## Assumptions and Limits",
            "\n".join(f"- {item}" for item in assumptions),
            references_markdown_block,
        ]
    ).strip() + "\n"

    sections_html = [
        (
            "Design Objective",
            (
                "<p>"
                f"This standalone note presents a focused preliminary mechanical design for reactor {reactor.reactor_id}, "
                f"the selected {reactor_basis.selected_reactor_type.lower()} used for the manufacture of {project_basis.target_product} "
                f"by {process_method}. The purpose of the note is to consolidate the process basis, shell and head sizing, "
                "agitation and shaft selection, jacket sizing, and the inlet/outlet nozzle schedule into one reactor-centered document."
                "</p>"
            ),
        ),
        ("Design Basis", _html_table(["Field", "Value"], basis_rows)),
        (
            "Process and Geometry Basis",
            _html_table(["Item", "Value"], geometry_rows)
            + "<p>The vessel geometry is tied to the solved v26 reactor basis. The straight-side shell length is kept from the current reactor design packet, while the head selection and nominal plate choices are rounded to practical fabrication values.</p>",
        ),
        (
            "Shell Thickness Calculation",
            _html_table(["Parameter", "Value"], shell_rows)
            + f"<p>The required shell thickness comes out to {_fmt(required_shell_thickness_mm, 3)} mm. For fabrication and corrosion margin, the shell is selected as {_fmt(adopted_shell_thickness_mm, 1)} mm nominal plate.</p>",
        ),
        (
            "Head Design Calculation",
            _html_table(["Parameter", "Value"], head_rows)
            + f"<p>A {head_type.lower()} arrangement is adopted. The calculated head thickness is {_fmt(required_head_thickness_mm, 3)} mm, and the selected nominal head thickness is {_fmt(adopted_head_thickness_mm, 1)} mm.</p>",
        ),
        (
            "Agitation System Design",
            _html_table(["Parameter", "Value"], agitation_rows)
            + f"<p>Because the reactor is tall and operates in low-viscosity liquid service, multiple axial-flow impellers are more appropriate than a single high-power radial turbine. The selected arrangement gives a turbulent agitation Reynolds number of about {_fmt(agitator_reynolds, 0)} and an absorbed agitation power of {_fmt(agitator_power_kw, 3)} kW.</p>",
        ),
        (
            "Shaft Design Calculation",
            _html_table(["Parameter", "Value"], shaft_rows)
            + f"<p>Using the agitator torque with a service factor of {service_factor:.2f}, the calculated solid-shaft diameter is {_fmt(required_shaft_diameter_m * 1000.0, 3)} mm. An adopted {_fmt(adopted_shaft_diameter_mm, 1)} mm shaft gives a practical preliminary selection for vendor detailing.</p>",
        ),
        (
            "Jacket Design Calculation",
            _html_table(["Parameter", "Value"], jacket_rows)
            + f"<p>The existing reactor duty requires approximately {_fmt(jacket_required_area_m2, 3)} m2 of effective transfer area. On a full-circumference shell basis this corresponds to about {_fmt(jacket_equivalent_height_m, 3)} m of active jacket coverage, so the standalone reactor design adopts a {_fmt(adopted_jacket_height_m, 3)} m effective jacketed zone for controllability and fabrication convenience.</p>",
        ),
        (
            "Reactor Nozzle Schedule",
            _html_table(["Service", "Basis", "Required ID (mm)", "Adopted NB (mm)", "Suggested Orientation"], nozzle_rows)
            + "<p>These nozzle sizes are reactor-specific preliminary values derived from actual process and utility flow criteria. They should be treated as the preferred nozzle schedule for the standalone reactor note, rather than the single global screening nozzle size carried in the broad equipment summary.</p>",
        ),
        ("Final Reactor Mechanical Specification", _html_table(["Item", "Selection"], final_spec_rows)),
        ("Assumptions and Limits", "<ul>" + "".join(f"<li>{item}</li>" for item in assumptions) + "</ul>"),
        ("References", _references_html(source_index, reactor_equipment.citations).replace("<h2>References</h2>", "")),
    ]
    html = _build_html_document(report_title, sections_html)

    project_dir = runner.store.project_dir(project_id)
    markdown_path = project_dir / "reactor_mechanical_design_report.md"
    html_path = project_dir / "reactor_mechanical_design_report.html"
    pdf_path = project_dir / "reactor_mechanical_design_report.pdf"

    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    render_styled_pdf(
        html,
        str(pdf_path),
        report_title,
        header_text=f"{project_basis.target_product} Reactor Mechanical Design",
    )
    return markdown_path, pdf_path
