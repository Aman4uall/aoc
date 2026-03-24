from __future__ import annotations

import re
import textwrap

import fitz

from aoc.models import (
    CalcTrace,
    ChapterArtifact,
    CostModel,
    DecisionRecord,
    EnergyBalance,
    EquipmentSpec,
    FinancialModel,
    HeatIntegrationStudyArtifact,
    IndianLocationDatum,
    ProcessSynthesisArtifact,
    ProcessTemplate,
    PropertyGapArtifact,
    ProductProfileArtifact,
    ProjectBasis,
    SourceRecord,
    StreamTable,
    UtilitySummaryArtifact,
    UtilityNetworkDecision,
    WorkingCapitalModel,
)


EG_CHAPTER_ORDER = [
    "executive_summary",
    "introduction_product_profile",
    "literature_survey",
    "process_selection",
    "market_capacity_selection",
    "site_selection",
    "thermodynamic_feasibility",
    "reaction_kinetics",
    "block_flow_diagram",
    "process_description",
    "material_balance",
    "energy_balance",
    "heat_integration_strategy",
    "reactor_design",
    "distillation_design",
    "equipment_design_sizing",
    "mechanical_design_moc",
    "storage_utilities",
    "instrumentation_control",
    "hazop",
    "safety_health_environment_waste",
    "layout",
    "project_cost",
    "cost_of_production",
    "working_capital",
    "financial_analysis",
    "conclusion",
]

GENERIC_CHAPTER_ORDER = [
    "executive_summary",
    "introduction_product_profile",
    "market_capacity_selection",
    "literature_survey",
    "process_selection",
    "site_selection",
    "thermodynamic_feasibility",
    "reaction_kinetics",
    "block_flow_diagram",
    "process_description",
    "material_balance",
    "energy_balance",
    "heat_integration_strategy",
    "equipment_design_sizing",
    "mechanical_design_moc",
    "storage_utilities",
    "instrumentation_control",
    "hazop",
    "safety_health_environment_waste",
    "layout",
    "project_cost",
    "cost_of_production",
    "working_capital",
    "financial_analysis",
    "conclusion",
]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator, *body])


def references_markdown(source_index: dict[str, SourceRecord]) -> str:
    lines = ["## References", ""]
    for source in sorted(source_index.values(), key=lambda item: item.title.lower()):
        location = source.url_or_doi or source.local_path or "Local source"
        domain = source.source_domain.value
        geo = source.geographic_label or source.geographic_scope.value
        year = source.reference_year or "n/a"
        lines.append(f"- **{source.source_id}**: {source.citation_text}. {location} [{domain}; {geo}; ref {year}]")
    return "\n".join(lines)


def _trace_table(title: str, traces: list[CalcTrace]) -> str:
    if not traces:
        return f"### {title}\n\nNo calculation traces recorded.\n"
    rows = [[trace.title, trace.formula, "; ".join(f"{key}={value}" for key, value in trace.substitutions.items()), f"{trace.result} {trace.units}".strip(), trace.notes] for trace in traces]
    return f"### {title}\n\n" + markdown_table(["Trace", "Formula", "Inputs", "Result", "Notes"], rows) + "\n"


def _decision_markdown(title: str, decision: DecisionRecord | None) -> str:
    if decision is None:
        return f"### {title}\n\nNo decision record captured.\n"
    rows = [
        [
            alternative.candidate_id,
            alternative.description,
            "yes" if alternative.feasible else "no",
            f"{alternative.total_score:.2f}",
            "; ".join(alternative.rejected_reasons) or "-",
        ]
        for alternative in decision.alternatives
    ]
    return (
        f"### {title}\n\n"
        + markdown_table(["Candidate", "Description", "Feasible", "Score", "Rejected Reasons"], rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]])
        + "\n"
    )


def annexures_markdown(
    product_profile: ProductProfileArtifact,
    property_gap: PropertyGapArtifact | None,
    process_synthesis: ProcessSynthesisArtifact | None,
    stream_table: StreamTable,
    equipment: list[EquipmentSpec],
    energy_balance: EnergyBalance,
    heat_integration_study: HeatIntegrationStudyArtifact | None,
    utility_network_decision: UtilityNetworkDecision | None,
    utility_summary: UtilitySummaryArtifact,
    cost_model: CostModel,
    working_capital: WorkingCapitalModel,
    financial: FinancialModel,
    route_decision: DecisionRecord | None,
    site_decision: DecisionRecord | None,
    utility_basis_decision: DecisionRecord | None,
    economic_basis_decision: DecisionRecord | None,
    sources: dict[str, SourceRecord],
    assumptions: list[str],
    calc_sections: list[tuple[str, list[CalcTrace]]],
    india_locations: list[IndianLocationDatum],
    extra_value_records,
) -> str:
    property_rows = [
        [item.name, item.value, item.units, item.method.value, ", ".join(item.supporting_sources or item.citations)]
        for item in product_profile.properties
    ]
    stream_rows: list[list[str]] = []
    for stream in stream_table.streams:
        for component in stream.components:
            stream_rows.append([stream.stream_id, stream.description, component.name, f"{component.mass_flow_kg_hr:.3f}", f"{component.molar_flow_kmol_hr:.6f}"])
    equipment_rows = [
        [item.equipment_id, item.equipment_type, item.service, f"{item.volume_m3:.3f}", f"{item.design_temperature_c:.1f}", f"{item.design_pressure_bar:.1f}", item.material_of_construction]
        for item in equipment
    ]
    utility_rows = [[item.utility_type, f"{item.load:.3f}", item.units, item.basis] for item in utility_summary.items]
    value_rows = [
        [item.name, item.value, item.units, item.provenance_method.value, item.sensitivity.value, "yes" if item.blocking else "no", ", ".join(item.source_ids)]
        for item in ([*(property_gap.values if property_gap else []), *extra_value_records])
    ]
    price_rows = [
        [datum.item_name, datum.category, datum.region, f"{datum.value_inr:,.2f}", datum.units, str(datum.reference_year), str(datum.normalization_year), ", ".join(datum.citations)]
        for datum in cost_model.india_price_data
    ]
    location_rows = [
        [location.site_name, location.state, location.port_access, location.utility_note, location.logistics_note, location.regulatory_note, str(location.reference_year), ", ".join(location.citations)]
        for location in india_locations
    ]
    source_rows = [[source.source_id, source.source_kind.value, source.source_domain.value, source.title, source.geographic_label or source.geographic_scope.value, (source.url_or_doi or source.local_path or "Local source")] for source in sources.values()]
    assumption_lines = [f"- {item}" for item in assumptions] or ["- No explicit assumptions recorded."]
    heat_rows: list[list[str]] = []
    for route_case in (heat_integration_study.route_decisions if heat_integration_study else []):
        for heat_case in route_case.cases:
            heat_rows.append(
                [
                    route_case.route_id,
                    heat_case.case_id,
                    heat_case.title,
                    f"{heat_case.recovered_duty_kw:.3f}",
                    f"{heat_case.residual_hot_utility_kw:.3f}",
                    f"{heat_case.annual_savings_inr:,.2f}",
                    f"{heat_case.payback_years:.3f}",
                    "yes" if heat_case.feasible else "no",
                ]
            )
    scenario_rows = [
        [item.scenario_name, f"{item.annual_utility_cost_inr:,.2f}", f"{item.annual_operating_cost_inr:,.2f}", f"{item.annual_revenue_inr:,.2f}", f"{item.gross_margin_inr:,.2f}"]
        for item in cost_model.scenario_results
    ]
    rejected_rows: list[list[str]] = []
    for decision in [
        process_synthesis.operating_mode_decision if process_synthesis else None,
        site_decision,
        route_decision,
        utility_basis_decision,
        economic_basis_decision,
    ]:
        if decision is None:
            continue
        for alternative in decision.alternatives:
            if alternative.rejected_reasons:
                rejected_rows.append([decision.decision_id, alternative.candidate_id, "; ".join(alternative.rejected_reasons)])

    sections = [
        "## Annexures",
        "",
        "### Property Table",
        markdown_table(["Property", "Value", "Units", "Method", "Sources"], property_rows),
        "",
        "### Value Provenance Table",
        markdown_table(["Name", "Value", "Units", "Method", "Sensitivity", "Blocking", "Sources"], value_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Stream Table",
        markdown_table(["Stream", "Description", "Component", "kg/h", "kmol/h"], stream_rows),
        "",
        "### Equipment Table",
        markdown_table(["ID", "Type", "Service", "Volume (m3)", "Design Temp (C)", "Design Pressure (bar)", "MoC"], equipment_rows),
        "",
        "### Utility Table",
        markdown_table(["Utility", "Load", "Units", "Basis"], utility_rows),
        "",
        "### India Price Evidence Log",
        markdown_table(["Item", "Category", "Region", "Value (INR)", "Units", "Ref year", "Norm year", "Sources"], price_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### India Location Evidence Log",
        markdown_table(["Site", "State", "Port access", "Utility note", "Logistics note", "Regulatory note", "Ref year", "Sources"], location_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Financial Snapshot",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Annual Revenue", f"{financial.currency} {financial.annual_revenue:,.2f}"],
                ["Annual Opex", f"{financial.currency} {financial.annual_operating_cost:,.2f}"],
                ["Gross Profit", f"{financial.currency} {financial.gross_profit:,.2f}"],
                ["Working Capital", f"INR {working_capital.working_capital_inr:,.2f}"],
                ["Payback (y)", f"{financial.payback_years:.3f}"],
                ["NPV", f"{financial.currency} {financial.npv:,.2f}"],
                ["IRR (%)", f"{financial.irr:.2f}"],
            ],
        ),
        "",
        "### Scenario Comparison Table",
        markdown_table(["Scenario", "Utility Cost (INR/y)", "Operating Cost (INR/y)", "Revenue (INR/y)", "Gross Margin (INR/y)"], scenario_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Heat Integration Cases",
        markdown_table(["Route", "Case ID", "Title", "Recovered Duty (kW)", "Residual Hot Utility (kW)", "Annual Savings (INR)", "Payback (y)", "Feasible"], heat_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        _decision_markdown("Operating Mode Decision", process_synthesis.operating_mode_decision if process_synthesis else None),
        "",
        _decision_markdown("Site Decision", site_decision),
        "",
        _decision_markdown("Route Decision", route_decision),
        "",
        _decision_markdown("Utility Basis Decision", utility_basis_decision),
        "",
        _decision_markdown("Economic Basis Decision", economic_basis_decision),
        "",
        "### Rejected Alternative Log",
        markdown_table(["Decision", "Candidate", "Reasons"], rejected_rows or [["n/a", "n/a", "n/a"]]),
        "",
        "### Source Extracts",
        markdown_table(["Source ID", "Kind", "Domain", "Title", "Geography", "Location"], source_rows),
        "",
    ]
    for title, traces in calc_sections:
        sections.append(_trace_table(title, traces))
        sections.append("")
    sections.extend(["### Major Assumptions", "\n".join(assumption_lines)])
    return "\n".join(sections)


def assemble_report(project_basis: ProjectBasis, chapters: list[ChapterArtifact], references_md: str, annexures_md: str) -> str:
    order = EG_CHAPTER_ORDER if project_basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA else GENERIC_CHAPTER_ORDER
    chapter_map = {chapter.chapter_id: chapter for chapter in chapters}
    ordered = [chapter_map[chapter_id] for chapter_id in order if chapter_id in chapter_map]
    toc_lines = [f"{index}. {chapter.title}" for index, chapter in enumerate(ordered, start=1)]
    body = [
        f"# {project_basis.target_product} Plant Design Report",
        "",
        f"- Capacity: {project_basis.capacity_tpa:.2f} TPA",
        f"- Purity target: {project_basis.target_purity_wt_pct:.2f} wt%",
        f"- Operating mode: {project_basis.operating_mode}",
        f"- Region / currency: {project_basis.region} / {project_basis.currency}",
        "",
        "## Table of Contents",
        "\n".join(toc_lines),
        "",
    ]
    for chapter in ordered:
        body.append(chapter.rendered_markdown.strip())
        body.append("")
    body.extend([references_md, "", annexures_md, ""])
    return "\n".join(body).strip() + "\n"


def render_pdf(markdown_text: str, output_path: str, title: str) -> str:
    clean_text = re.sub(r"`", "", markdown_text)
    clean_text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", clean_text)
    lines: list[str] = []
    for paragraph in clean_text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        prefix = ""
        text = paragraph
        if paragraph.startswith("#"):
            hashes = len(paragraph) - len(paragraph.lstrip("#"))
            prefix = " " * max(0, hashes - 1)
            text = paragraph.lstrip("#").strip().upper()
        lines.extend(prefix + part for part in textwrap.wrap(text, width=92))
    document = fitz.open()
    page = document.new_page()
    page.set_mediabox(fitz.Rect(0, 0, 595, 842))
    y = 48
    for line in lines:
        if y > 790:
            page = document.new_page()
            page.set_mediabox(fitz.Rect(0, 0, 595, 842))
            y = 48
        page.insert_text((48, y), line, fontsize=10, fontname="cour")
        y += 12 if line else 8
    document.set_metadata({"title": title})
    document.save(output_path)
    document.close()
    return output_path
