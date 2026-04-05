from __future__ import annotations

from datetime import date
import os
import re
import tempfile
import textwrap

import fitz

from aoc.models import (
    AgentDecisionFabricArtifact,
    BenchmarkManifest,
    CalcTrace,
    ChapterArtifact,
    ColumnHydraulics,
    ControlArchitectureDecision,
    CostModel,
    CriticRegistryArtifact,
    DebtSchedule,
    DecisionRecord,
    EconomicScenarioModel,
    EnergyBalance,
    EquipmentSpec,
    FinancialModel,
    FinancialSchedule,
    FlowsheetGraph,
    FlowsheetCase,
    HazopNodeRegister,
    HeatExchangerThermalDesign,
    HeatIntegrationStudyArtifact,
    IndianLocationDatum,
    MechanicalDesignArtifact,
    MechanicalDesignBasis,
    OperationsPlanningArtifact,
    PlantCostSummary,
    PumpDesign,
    ProcessArchetype,
    ProcessSynthesisArtifact,
    ProcessTemplate,
    PropertyGapArtifact,
    ProductProfileArtifact,
    ReactorDesignBasis,
    ReactionSystem,
    ProjectBasis,
    ResolvedSourceSet,
    ResolvedValueArtifact,
    RouteFamilyArtifact,
    RouteSurveyArtifact,
    SolveResult,
    SparseDataPolicyArtifact,
    SourceRecord,
    StreamTable,
    TaxDepreciationBasis,
    UtilitySummaryArtifact,
    UtilityArchitectureDecision,
    UtilityNetworkDecision,
    UnitOperationFamilyArtifact,
    WorkingCapitalModel,
)
from aoc.properties.models import MixturePropertyArtifact, PropertyPackageArtifact, PropertyRequirementSet, SeparationThermoArtifact


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
    "process_flow_diagram",
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
    "data_gaps_estimation_methods",
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
    "process_flow_diagram",
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
    "data_gaps_estimation_methods",
    "conclusion",
]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator, *body])


def _project_table_rows(headers: list[str], rows: list[list[str]], selected_headers: list[str]) -> list[list[str]]:
    header_positions = {header: index for index, header in enumerate(headers)}
    return [
        [
            row[header_positions[header]] if header in header_positions and header_positions[header] < len(row) else "n/a"
            for header in selected_headers
        ]
        for row in rows
    ]


def _narrow_table_section(title: str, headers: list[str], rows: list[list[str]], selected_headers: list[str]) -> str:
    return f"### {title}\n\n" + markdown_table(selected_headers, _project_table_rows(headers, rows, selected_headers)) + "\n"


def _normalized_heading_label(heading_text: str) -> str:
    label = re.sub(r"^#+\s*", "", heading_text).strip()
    label = re.sub(r"^\d+\.\s*", "", label).strip()
    return label or "Report Section"


def _strip_leading_heading(markdown_text: str, heading_prefix: str) -> str:
    lines = markdown_text.splitlines()
    if lines and lines[0].strip().startswith(heading_prefix):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def _is_markdown_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    first = lines[index].strip()
    second = lines[index + 1].strip()
    return first.startswith("|") and second.startswith("|") and "---" in second


def _last_non_empty_line(lines: list[str]) -> str:
    for line in reversed(lines):
        if line.strip():
            return line.strip()
    return ""


def _apply_caption_numbering(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: list[str] = []
    current_heading = "Report Section"
    table_counter = 0
    figure_counter = 0

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            current_heading = _normalized_heading_label(stripped)
            output.append(line)
            continue
        if _is_markdown_table_start(lines, index):
            previous = _last_non_empty_line(output)
            if not previous.startswith("**Table "):
                table_counter += 1
                output.extend([f"**Table {table_counter}. {current_heading}**", ""])
            output.append(line)
            continue
        if stripped.startswith("```mermaid") or stripped.startswith("```diagram-svg"):
            previous = _last_non_empty_line(output)
            if not previous.startswith("**Figure "):
                figure_counter += 1
                output.extend([f"**Figure {figure_counter}. {current_heading}**", ""])
            output.append(line)
            continue
        output.append(line)
    return "\n".join(output)


def _caption_register_lines(markdown_text: str, caption_prefix: str) -> list[str]:
    lines: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"**{caption_prefix} ") and stripped.endswith("**"):
            lines.append(stripped.strip("*"))
    return lines


def _build_caption_register_sections(markdown_text: str) -> str:
    table_lines = _caption_register_lines(markdown_text, "Table")
    figure_lines = _caption_register_lines(markdown_text, "Figure")
    table_entries = [f"- {line}" for line in table_lines] or ["- No numbered tables captured."]
    figure_entries = [f"- {line}" for line in figure_lines] or ["- No numbered figures captured."]
    sections = [
        "## List of Tables",
        "",
        *table_entries,
        "",
        "## List of Figures",
        "",
        *figure_entries,
    ]
    return "\n".join(sections).strip()


def _replace_once(markdown_text: str, target: str, replacement: str) -> str:
    return markdown_text.replace(target, replacement, 1) if target in markdown_text else markdown_text


def _format_appendix_bundle(markdown_text: str) -> str:
    appendix_body = markdown_text.strip()
    appendix_heading_pairs = [
        ("### Appendix A: Material Safety Data Sheet", "## Appendix A: Material Safety Data Sheet"),
        ("### Appendix B: Python Code and Reproducibility Bundle", "## Appendix B: Python Code and Reproducibility Bundle"),
        ("### Appendix C: Process Design Data Sheet", "## Appendix C: Process Design Data Sheet"),
    ]
    for original, promoted in appendix_heading_pairs:
        appendix_body = _replace_once(appendix_body, original, promoted)
        appendix_body = _replace_once(appendix_body, promoted, f"---\n\n{promoted}")

    annexure_groups = [
        ("### Benchmark Manifest", "## Annexure I: Evidence and Source Basis"),
        ("### Property Table", "## Annexure II: Property and Thermodynamic Registers"),
        ("### Reaction Extent Set", "## Annexure III: Process, Decision, and Critic Registers"),
        ("### Stream Table", "## Annexure IV: Streams, Flowsheet, and Solver Registers"),
        ("### Equipment Table", "## Annexure V: Equipment, Utility, and Financial Registers"),
    ]
    for marker, heading in annexure_groups:
        appendix_body = _replace_once(appendix_body, marker, f"---\n\n{heading}\n\n{marker}")

    navigation_lines = [
        "## Appendix Navigation",
        "",
        "The appendix package is organized into report-style appendices followed by grouped annexure registers for evidence, properties, flowsheet state, and design backup.",
        "",
        "- Appendix A: Material Safety Data Sheet",
        "- Appendix B: Python Code and Reproducibility Bundle",
        "- Appendix C: Process Design Data Sheet",
        "- Annexure I: Evidence and Source Basis",
        "- Annexure II: Property and Thermodynamic Registers",
        "- Annexure III: Process, Decision, and Critic Registers",
        "- Annexure IV: Streams, Flowsheet, and Solver Registers",
        "- Annexure V: Equipment, Utility, and Financial Registers",
    ]
    return "\n".join([*navigation_lines, "", appendix_body]).strip()


def references_markdown(source_index: dict[str, SourceRecord]) -> str:
    lines = ["## References", ""]
    for index, source in enumerate(sorted(source_index.values(), key=lambda item: item.title.lower()), start=1):
        organization = (source.citation_text or "").split(".", 1)[0].strip() or source.source_id
        title = source.title.strip().rstrip(".")
        year = str(source.reference_year) if source.reference_year else "n.d."
        location = source.url_or_doi or source.local_path or "Local source"
        geo = source.geographic_label or source.geographic_scope.value
        domain = source.source_domain.value.replace("_", " ")
        lines.append(
            f"{index}. {organization}. *{title}*. {year}. "
            f"Available at: {location}. "
            f"[Source ID: {source.source_id}; Domain: {domain}; Geography: {geo}]"
        )
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
    benchmark_manifest: BenchmarkManifest | None,
    resolved_sources: ResolvedSourceSet | None,
    product_profile: ProductProfileArtifact,
    route_survey: RouteSurveyArtifact | None,
    reaction_system: ReactionSystem | None,
    property_gap: PropertyGapArtifact | None,
    resolved_values: ResolvedValueArtifact | None,
    property_packages: PropertyPackageArtifact | None,
    property_requirements: PropertyRequirementSet | None,
    separation_thermo: SeparationThermoArtifact | None,
    process_archetype: ProcessArchetype | None,
    route_families: RouteFamilyArtifact | None,
    unit_operation_family: UnitOperationFamilyArtifact | None,
    sparse_data_policy: SparseDataPolicyArtifact | None,
    process_synthesis: ProcessSynthesisArtifact | None,
    operations_planning: OperationsPlanningArtifact | None,
    agent_fabric: AgentDecisionFabricArtifact | None,
    critic_registry: CriticRegistryArtifact | None,
    stream_table: StreamTable,
    mixture_properties: MixturePropertyArtifact | None,
    flowsheet_graph: FlowsheetGraph | None,
    flowsheet_case: FlowsheetCase | None,
    solve_result: SolveResult | None,
    equipment: list[EquipmentSpec],
    energy_balance: EnergyBalance,
    heat_integration_study: HeatIntegrationStudyArtifact | None,
    utility_network_decision: UtilityNetworkDecision | None,
    utility_architecture: UtilityArchitectureDecision | None,
    utility_summary: UtilitySummaryArtifact,
    mechanical_design: MechanicalDesignArtifact | None,
    mechanical_design_basis: MechanicalDesignBasis | None,
    control_architecture: ControlArchitectureDecision | None,
    hazop_register: HazopNodeRegister | None,
    cost_model: CostModel,
    plant_cost_summary: PlantCostSummary | None,
    working_capital: WorkingCapitalModel,
    financial: FinancialModel,
    debt_schedule: DebtSchedule | None,
    tax_depreciation_basis: TaxDepreciationBasis | None,
    financial_schedule: FinancialSchedule | None,
    economic_scenarios: EconomicScenarioModel | None,
    route_decision: DecisionRecord | None,
    site_decision: DecisionRecord | None,
    utility_basis_decision: DecisionRecord | None,
    economic_basis_decision: DecisionRecord | None,
    extra_decisions: list[DecisionRecord],
    sources: dict[str, SourceRecord],
    assumptions: list[str],
    calc_sections: list[tuple[str, list[CalcTrace]]],
    india_locations: list[IndianLocationDatum],
    reactor_design_basis: ReactorDesignBasis | None,
    column_hydraulics: ColumnHydraulics | None,
    exchanger_thermal: HeatExchangerThermalDesign | None,
    pump_design: PumpDesign | None,
    equipment_datasheets_markdown: str | None,
    extra_value_records,
) -> str:
    property_rows = [
        [item.name, item.value, item.units, item.method.value, ", ".join(item.supporting_sources or item.citations)]
        for item in product_profile.properties
    ]
    reaction_extent_rows = [
        [
            extent.extent_id,
            extent.kind,
            extent.representative_component or "-",
            f"{extent.extent_fraction_of_converted_feed:.6f}",
            extent.status,
        ]
        for extent in (reaction_system.reaction_extent_set.extents if reaction_system and reaction_system.reaction_extent_set else [])
    ]
    byproduct_closure_rows = [
        [
            estimate.component_name,
            estimate.basis,
            f"{estimate.allocation_fraction:.6f}",
            estimate.provenance,
            estimate.status,
        ]
        for estimate in (reaction_system.byproduct_closure.estimates if reaction_system and reaction_system.byproduct_closure else [])
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
    mechanical_rows = [
        [
            item.equipment_id,
            item.equipment_type,
            f"{item.shell_thickness_mm:.2f}",
            f"{item.head_thickness_mm:.2f}",
            item.pressure_class,
            f"{item.hydrotest_pressure_bar:.2f}",
            f"{item.nozzle_diameter_mm:.1f}",
            item.support_type,
            item.support_load_case,
            f"{item.support_thickness_mm:.2f}",
            f"{item.operating_load_kn:.2f}",
            f"{item.wind_load_kn:.2f}",
            f"{item.seismic_load_kn:.2f}",
            f"{item.piping_load_kn:.2f}",
            f"{item.thermal_growth_mm:.2f}",
            f"{item.nozzle_reinforcement_area_mm2:.1f}",
            item.support_variant or item.support_type,
            str(item.anchor_group_count),
            f"{item.foundation_footprint_m2:.2f}",
            f"{item.maintenance_clearance_m:.2f}",
            "yes" if item.access_ladder_required else "no",
            "yes" if item.lifting_lug_required else "no",
            item.nozzle_reinforcement_family or "n/a",
            f"{item.local_shell_load_interaction_factor:.2f}",
            "yes" if item.maintenance_platform_required else "no",
            f"{item.platform_area_m2:.2f}",
        ]
        for item in (mechanical_design.items if mechanical_design else [])
    ]
    value_rows = [
        [item.name, item.value, item.units, item.provenance_method.value, item.sensitivity.value, "yes" if item.blocking else "no", ", ".join(item.source_ids)]
        for item in ([*(property_gap.values if property_gap else []), *extra_value_records])
    ]
    resolved_value_rows = [
        [item.name, str(item.resolution_level), item.resolution_status, item.sensitivity.value, item.selected_source_id or "-", item.justification]
        for item in (resolved_values.values if resolved_values else [])
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
    selected_route = None
    if route_survey:
        selected_route_id = route_decision.selected_candidate_id if route_decision is not None else None
        selected_route = next((route for route in route_survey.routes if route.route_id == selected_route_id), None)
        if selected_route is None and route_survey.routes:
            selected_route = route_survey.routes[0]
    msds_rows: list[list[str]] = []
    if selected_route is not None:
        primary_hazard = selected_route.hazards[0].description if selected_route.hazards else (
            f"{process_archetype.hazard_intensity.title()} hazard screening basis." if process_archetype else "Process hazard basis not explicitly classified."
        )
        primary_safeguard = selected_route.hazards[0].safeguard if selected_route.hazards else "Contained handling, isolation, and compatible storage basis."
        seen_materials: set[str] = set()
        for participant in selected_route.participants:
            if participant.name in seen_materials:
                continue
            seen_materials.add(participant.name)
            if participant.role == "product":
                hazard_basis = "; ".join(product_profile.safety_notes[:2]) or primary_hazard
                handling_basis = product_profile.safety_notes[0] if product_profile.safety_notes else primary_safeguard
            else:
                hazard_basis = primary_hazard
                handling_basis = primary_safeguard
            msds_rows.append(
                [
                    participant.name,
                    participant.role.title(),
                    participant.formula or "-",
                    hazard_basis,
                    handling_basis,
                    "Contained transfer, routine PPE, emergency isolation, and plant-response procedures per the SHE chapter.",
                ]
            )
    if not msds_rows:
        msds_rows = [
            [
                product_profile.product_name,
                "Product",
                "-",
                "; ".join(product_profile.safety_notes[:2]) or "Product safety basis not explicitly resolved.",
                product_profile.safety_notes[0] if product_profile.safety_notes else "Use contained handling and compatible storage.",
                "Contained transfer, routine PPE, and emergency isolation according to the plant SHE basis.",
            ]
        ]
    appendix_code_rows = [
        ["Pipeline entry", "aoc/pipeline.py", "Stage orchestration, chapter generation, final report assembly"],
        ["Engineering calculators", "aoc/calculators.py", "Core process calculations and artifact builders"],
        ["Unit-operation solvers", "aoc/solvers/units.py", "Reactor, separation, hydraulic, solids, and package design logic"],
        ["Economics engine", "aoc/economics_v2.py", "Project cost, working capital, financing, and schedules"],
        ["Property engine", "aoc/properties/engine.py", "Pure-component and phase-equilibrium property routing"],
        ["Report publisher", "aoc/publish.py", "Markdown assembly, annexures, and PDF rendering support"],
    ]
    appendix_artifact_rows = [
        ["Benchmark manifest", benchmark_manifest.benchmark_id if benchmark_manifest else "n/a", "Benchmark/report parity contract basis"],
        ["Resolved values", str(len(resolved_values.values) if resolved_values else 0), "Cited and estimated value basis carried into the report"],
        ["Stream table", str(len(stream_table.streams)), "Material-balance stream ledger and composition basis"],
        ["Equipment list", str(len(equipment)), "Equipment inventory for sizing, cost, and datasheets"],
        ["Calc trace sections", str(len(calc_sections)), "Trace bundle captured for engineering auditability"],
        ["Financial schedule rows", str(len(financial_schedule.lines) if financial_schedule else 0), "Typed multi-year finance schedule"],
    ]
    source_resolution_rows = []
    for group in (resolved_sources.groups if resolved_sources else []):
        for candidate in group.candidates:
            source_resolution_rows.append(
                [
                    group.source_domain.value,
                    candidate.source_id,
                    f"{candidate.total_score:.1f}",
                    "yes" if candidate.source_id in group.selected_source_ids else "no",
                    "yes" if group.unresolved_conflict else "no",
                ]
            )
    source_conflict_rows = [
        [
            conflict.source_domain.value,
            conflict.selected_source_id or "-",
            ", ".join(conflict.competing_source_ids) or "-",
            f"{conflict.score_gap:.2f}",
            "yes" if conflict.blocking else "no",
            conflict.recommended_resolution,
        ]
        for conflict in (resolved_sources.conflicts if resolved_sources else [])
    ]
    property_estimate_rows = [
        [
            estimate.property_name,
            estimate.selected_method.value,
            ", ".join(method.value for method in estimate.candidate_methods),
            estimate.selected_source_id or "-",
            estimate.sensitivity.value,
            "yes" if estimate.blocking else "no",
        ]
        for estimate in (resolved_values.property_estimates if resolved_values else [])
    ]
    property_identifier_rows = [
        [
            identifier.identifier_id,
            identifier.canonical_name,
            identifier.formula or "-",
            identifier.cas_number or "-",
            ", ".join(identifier.route_ids) or "-",
            identifier.resolution_status,
        ]
        for identifier in (property_packages.identifiers if property_packages else [])
    ]
    pure_component_rows = []
    property_correlation_rows = []
    binary_interaction_rows = []
    henry_rows = []
    solubility_rows = []
    if property_packages:
        for package in property_packages.packages:
            for label, prop in [
                ("molecular_weight", package.molecular_weight),
                ("normal_boiling_point", package.normal_boiling_point),
                ("melting_point", package.melting_point),
                ("liquid_density", package.liquid_density),
                ("liquid_viscosity", package.liquid_viscosity),
                ("liquid_heat_capacity", package.liquid_heat_capacity),
                ("heat_of_vaporization", package.heat_of_vaporization),
                ("thermal_conductivity", package.thermal_conductivity),
            ]:
                if prop is None:
                    continue
                pure_component_rows.append(
                    [
                        package.identifier.canonical_name,
                        label,
                        prop.value,
                        prop.units,
                        str(prop.reference_temperature_c) if prop.reference_temperature_c is not None else "-",
                        prop.provenance_method.value,
                        prop.resolution_status,
                        ", ".join(prop.source_ids) or "-",
                    ]
                )
        for correlation in property_packages.correlations:
            property_correlation_rows.append(
                [
                    correlation.identifier_id,
                    correlation.property_name,
                    correlation.equation_name,
                    ", ".join(f"{key}={value}" for key, value in correlation.parameters.items()) or "-",
                    str(correlation.temperature_min_c) if correlation.temperature_min_c is not None else "-",
                    str(correlation.temperature_max_c) if correlation.temperature_max_c is not None else "-",
                    correlation.provenance_method.value,
                    ", ".join(correlation.source_ids) or "-",
                ]
            )
        for bip in property_packages.binary_interaction_parameters:
            binary_interaction_rows.append(
                [
                    bip.component_a_name,
                    bip.component_b_name,
                    bip.model_name,
                    f"{bip.tau12:.6f}" if bip.tau12 is not None else "-",
                    f"{bip.tau21:.6f}" if bip.tau21 is not None else "-",
                    f"{bip.alpha12:.6f}" if bip.alpha12 is not None else "-",
                    bip.resolution_status,
                    ", ".join(bip.source_ids) or "-",
                ]
            )
        for constant in property_packages.henry_law_constants:
            henry_rows.append(
                [
                    constant.gas_component_name,
                    constant.solvent_component_name,
                    f"{constant.value:.6f}",
                    constant.units,
                    str(constant.reference_temperature_c) if constant.reference_temperature_c is not None else "-",
                    constant.equation_form,
                    constant.resolution_status,
                    ", ".join(constant.source_ids) or "-",
                ]
            )
        for curve in property_packages.solubility_curves:
            solubility_rows.append(
                [
                    curve.solute_component_name,
                    curve.solvent_component_name,
                    curve.equation_name,
                    ", ".join(f"{key}={value}" for key, value in curve.parameters.items()) or "-",
                    str(curve.temperature_min_c) if curve.temperature_min_c is not None else "-",
                    str(curve.temperature_max_c) if curve.temperature_max_c is not None else "-",
                    curve.units,
                    curve.resolution_status,
                    ", ".join(curve.source_ids) or "-",
                ]
            )
    requirement_rows = [
        [
            item.stage_id,
            item.identifier_id,
            item.property_name,
            item.status,
            "yes" if item.allow_estimated else "no",
            "yes" if item.blocking else "no",
        ]
        for item in (property_requirements.coverage if property_requirements else [])
    ]
    separation_thermo_rows = [
        ["Family", separation_thermo.separation_family],
        ["Pressure (bar)", f"{separation_thermo.system_pressure_bar:.3f}"],
        ["Light key", separation_thermo.light_key],
        ["Heavy key", separation_thermo.heavy_key],
        ["Activity model", separation_thermo.activity_model],
        ["Top temperature (C)", f"{separation_thermo.nominal_top_temp_c:.3f}"],
        ["Bottom temperature (C)", f"{separation_thermo.nominal_bottom_temp_c:.3f}"],
        ["Average alpha", f"{separation_thermo.relative_volatility.average_alpha:.6f}" if separation_thermo.relative_volatility else "n/a"],
        ["Method", separation_thermo.relative_volatility.method if separation_thermo.relative_volatility else "n/a"],
        ["Missing BIP pairs", ", ".join(separation_thermo.missing_binary_pairs) or "none"],
    ] if separation_thermo else []
    separation_thermo_component_rows = [
        [
            top.component_name,
            f"{top.temperature_c:.1f}",
            f"{top.activity_coefficient:.6f}",
            f"{top.k_value:.6f}",
            top.method,
            f"{bottom.temperature_c:.1f}",
            f"{bottom.activity_coefficient:.6f}",
            f"{bottom.k_value:.6f}",
            bottom.method,
        ]
        for top, bottom in zip(
            separation_thermo.top_k_values if separation_thermo else [],
            separation_thermo.bottom_k_values if separation_thermo else [],
        )
    ]
    unresolved_property_rows = [
        [
            package.identifier.canonical_name,
            property_name,
            package.resolution_status,
            "yes" if property_name in package.blocked_properties else "no",
        ]
        for package in (property_packages.packages if property_packages else [])
        for property_name in package.blocked_properties
    ]
    archetype_rows = []
    if process_archetype:
        archetype_rows = [
            ["Archetype ID", process_archetype.archetype_id],
            ["Compound family", process_archetype.compound_family],
            ["Product phase", process_archetype.dominant_product_phase],
            ["Feed phase", process_archetype.dominant_feed_phase],
            ["Separation family", process_archetype.dominant_separation_family],
            ["Heat profile", process_archetype.heat_management_profile],
            ["Hazard intensity", process_archetype.hazard_intensity],
            ["Benchmark profile", process_archetype.benchmark_profile or "custom"],
        ]
    route_family_rows = [
        [
            profile.route_id,
            profile.family_label,
            profile.primary_reactor_class,
            profile.primary_separation_train,
            profile.heat_recovery_style,
            f"{profile.maturity_score:.2f}",
            f"{profile.india_fit_score:.2f}",
            ", ".join(profile.critic_flags[:3]) or "-",
            profile.india_deployment_blocker or "none",
        ]
        for profile in (route_families.profiles if route_families else [])
    ]
    unit_operation_family_rows = [
        [candidate.service_group, candidate.candidate_id, candidate.applicability_status, f"{candidate.applicability_score:.2f}", candidate.description]
        for candidate in ([*(unit_operation_family.reactor_candidates if unit_operation_family else []), *(unit_operation_family.separation_candidates if unit_operation_family else [])])
    ]
    unit_operation_support_rows = [
        ["Route", unit_operation_family.route_id if unit_operation_family else "n/a"],
        ["Route family", unit_operation_family.route_family_label if unit_operation_family else "n/a"],
        ["Dominant phase pattern", unit_operation_family.dominant_phase_pattern if unit_operation_family else "n/a"],
        ["Supporting operations", ", ".join(unit_operation_family.supporting_unit_operations) if unit_operation_family else "n/a"],
        ["Applicability critics", ", ".join(unit_operation_family.applicability_critics) if unit_operation_family else "n/a"],
    ]
    sparse_policy_rows = [
        [
            rule.stage_id,
            rule.subject,
            rule.artifact_family,
            "yes" if rule.allow_estimated else "no",
            "yes" if rule.allow_analogy else "no",
            "yes" if rule.allow_heuristic_fallback else "no",
            f"{rule.minimum_confidence:.2f}",
            rule.current_status,
            ", ".join(rule.triggered_items[:3]) or "-",
        ]
        for rule in (sparse_data_policy.rules if sparse_data_policy else [])
    ]
    operations_rows = [
        ["Service family", operations_planning.service_family],
        ["Recommended mode", operations_planning.recommended_operating_mode],
        ["Availability policy", operations_planning.availability_policy_label],
        ["Raw-material buffer (d)", f"{operations_planning.raw_material_buffer_days:.3f}"],
        ["Finished-goods buffer (d)", f"{operations_planning.finished_goods_buffer_days:.3f}"],
        ["Operating stock (d)", f"{operations_planning.operating_stock_days:.3f}"],
        ["Restart buffer (d)", f"{operations_planning.restart_buffer_days:.3f}"],
        ["Startup ramp (d)", f"{operations_planning.startup_ramp_days:.3f}"],
        ["Campaign length (d)", f"{operations_planning.campaign_length_days:.3f}"],
        ["Cleaning cycle (d)", f"{operations_planning.cleaning_cycle_days:.3f}"],
        ["Cleaning downtime (d)", f"{operations_planning.cleaning_downtime_days:.3f}"],
        ["Throughput loss fraction", f"{operations_planning.throughput_loss_fraction:.6f}"],
        ["Restart loss fraction", f"{operations_planning.restart_loss_fraction:.6f}"],
        ["Annual restart loss (kg/y)", f"{operations_planning.annual_restart_loss_kg:,.3f}"],
    ] if operations_planning else []
    flowsheet_rows = [
        [node.node_id, node.unit_type, ", ".join(node.upstream_nodes) or "-", ", ".join(node.downstream_nodes) or "-", ", ".join(node.representative_stream_ids) or "-"]
        for node in (flowsheet_graph.nodes if flowsheet_graph else [])
    ]
    flowsheet_case_rows = [
        [
            unit.unit_id,
            unit.unit_type,
            ", ".join(unit.upstream_stream_ids) or "-",
            ", ".join(unit.downstream_stream_ids) or "-",
            unit.closure_status,
            unit.coverage_status,
            ", ".join(unit.unresolved_sensitivities[:3]) or "-",
        ]
        for unit in (flowsheet_case.units if flowsheet_case else [])
    ]
    composition_state_rows = [
        [
            state.unit_id,
            state.unit_type,
            state.dominant_inlet_phase or "-",
            state.dominant_outlet_phase or "-",
            ", ".join(name for name, _ in sorted(state.outlet_component_mole_fraction.items(), key=lambda item: item[1], reverse=True)[:3]) or "-",
            state.status,
        ]
        for state in (stream_table.composition_states if stream_table else [])
    ]
    composition_closure_rows = [
        [
            closure.unit_id,
            "yes" if closure.reactive else "no",
            f"{closure.inlet_fraction_sum:.6f}",
            f"{closure.outlet_fraction_sum:.6f}",
            f"{closure.composition_error_pct:.6f}",
            closure.closure_status,
        ]
        for closure in (stream_table.composition_closures if stream_table else [])
    ]
    mixture_rows = [
        [
            package.unit_id,
            package.dominant_phase or "-",
            f"{package.liquid_heat_capacity_kj_kg_k:.6f}" if package.liquid_heat_capacity_kj_kg_k is not None else "-",
            f"{package.liquid_density_kg_m3:.6f}" if package.liquid_density_kg_m3 is not None else "-",
            f"{package.liquid_viscosity_pa_s:.8f}" if package.liquid_viscosity_pa_s is not None else "-",
            package.resolution_status,
            ", ".join(package.estimated_properties) or "-",
        ]
        for package in (mixture_properties.packages if mixture_properties else [])
    ]
    solve_rows = [
        [
            unit_id,
            f"{closure:.6f}",
            solve_result.unitwise_status.get(unit_id, "estimated"),
            solve_result.unitwise_coverage_status.get(unit_id, "partial"),
            ", ".join(solve_result.unitwise_unresolved_sensitivities.get(unit_id, [])[:3]) or "-",
        ]
        for unit_id, closure in (solve_result.unitwise_closure.items() if solve_result else {})
    ]
    phase_split_rows = [
        [
            spec.unit_id,
            spec.separation_family,
            spec.mechanism,
            ", ".join(spec.inlet_phases) or "-",
            spec.product_phase_target or "-",
            spec.waste_phase_target or "-",
            spec.recycle_phase_target or "-",
            spec.phase_split_status,
        ]
        for spec in (stream_table.phase_split_specs if stream_table else [])
    ]
    separator_performance_rows = [
        [
            perf.unit_id,
            perf.separation_family,
            perf.performance_status,
            f"{perf.product_mass_fraction:.6f}",
            f"{perf.waste_mass_fraction:.6f}",
            f"{perf.recycle_mass_fraction:.6f}",
            f"{perf.split_closure_pct:.6f}",
        ]
        for perf in (stream_table.separator_performances if stream_table else [])
    ]
    recycle_convergence_rows = [
        [
            summary.loop_id,
            summary.recycle_source_unit_id or "-",
            summary.convergence_status,
            f"{summary.max_component_error_pct:.6f}",
            f"{summary.mean_component_error_pct:.6f}",
            str(summary.max_iterations),
            ", ".join(f"{family}={value:.3f}" for family, value in sorted(summary.purge_policy_by_family.items())) or "-",
        ]
        for summary in (stream_table.convergence_summaries if stream_table else [])
    ]
    benchmark_rows = []
    if benchmark_manifest:
        benchmark_rows = [
            ["Benchmark ID", benchmark_manifest.benchmark_id],
            ["Target product", benchmark_manifest.target_product],
            ["Archetype family", benchmark_manifest.archetype_family],
            ["Expected decisions", ", ".join(benchmark_manifest.expected_decisions)],
            ["Required source domains", ", ".join(domain.value for domain in benchmark_manifest.required_public_source_domains)],
        ]
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
        [
            item.scenario_name,
            f"{item.annual_utility_cost_inr:,.2f}",
            f"{item.annual_transport_service_cost_inr:,.2f}",
            f"{item.annual_utility_island_operating_burden_inr:,.2f}",
            f"{item.annual_operating_cost_inr:,.2f}",
            f"{item.annual_revenue_inr:,.2f}",
            f"{item.gross_margin_inr:,.2f}",
        ]
        for item in cost_model.scenario_results
    ]
    utility_island_economic_rows = [
        [
            item.island_id,
            item.topology,
            f"{item.shared_htm_inventory_m3:.3f}",
            f"{item.header_design_pressure_bar:.2f}",
            f"{item.condenser_reboiler_pair_score:.3f}",
            f"{item.control_complexity_factor:.3f}",
            f"{item.maintenance_cycle_years:.2f}",
            f"{item.replacement_event_cost_inr:,.2f}",
            f"{item.annualized_replacement_cost_inr:,.2f}",
            f"{item.planned_turnaround_days:.2f}",
            f"{item.project_capex_burden_inr:,.2f}",
            f"{item.annual_allocated_utility_cost_inr:,.2f}",
            f"{item.annual_service_cost_inr:,.2f}",
            f"{item.annual_operating_burden_inr:,.2f}",
            f"{item.utility_cost_share_fraction:.3f}",
            f"{item.capex_share_fraction:.3f}",
        ]
        for item in cost_model.utility_island_costs
    ]
    utility_island_scenario_rows = [
        [
            scenario.scenario_name,
            impact.island_id,
            f"{impact.project_capex_burden_inr:,.2f}",
            f"{impact.annual_allocated_utility_cost_inr:,.2f}",
            f"{impact.annual_service_cost_inr:,.2f}",
            f"{impact.annual_replacement_cost_inr:,.2f}",
            f"{impact.annual_operating_burden_inr:,.2f}",
        ]
        for scenario in cost_model.scenario_results
        for impact in scenario.utility_island_impacts
    ]
    equipment_cost_rows = [
        [
            item.equipment_id,
            item.equipment_type,
            f"{item.bare_cost_inr:,.2f}",
            f"{item.installed_cost_inr:,.2f}",
            f"{item.spares_cost_inr:,.2f}",
            item.procurement_package_family or "n/a",
            f"{item.procurement_lead_time_months:.2f}",
            f"{item.import_duty_inr:,.2f}",
            item.basis,
        ]
        for item in cost_model.equipment_cost_items
    ]
    plant_cost_rows = [
        [
            item.equipment_id,
            f"{item.bare_cost_inr:,.2f}",
            f"{item.installation_inr:,.2f}",
            f"{item.piping_inr:,.2f}",
            f"{item.instrumentation_inr:,.2f}",
            f"{item.total_installed_inr:,.2f}",
        ]
        for item in (plant_cost_summary.equipment_breakdowns if plant_cost_summary else [])
    ]
    procurement_rows = [
        [
            str(item.get("package_family", "")),
            str(item.get("milestone", "")),
            f"{float(item.get('month', 0.0)):.1f}",
            f"{float(item.get('draw_fraction', 0.0)):.3f}",
            f"{float(item.get('capex_draw_inr', 0.0)):,.2f}",
        ]
        for item in cost_model.procurement_schedule
    ]
    procurement_package_rows = [
        [
            item.package_id,
            item.equipment_type,
            item.package_family,
            f"{item.lead_time_months:.2f}",
            f"{item.award_month:.2f}",
            f"{item.delivery_month:.2f}",
            f"{item.import_content_fraction:.3f}",
            f"{item.import_duty_fraction:.3f}",
            f"{item.import_duty_inr:,.2f}",
            f"{item.capex_burden_inr:,.2f}",
        ]
        for item in cost_model.procurement_package_impacts
    ]
    schedule_rows = [
        [
            str(item["year"]),
            f'{item["capacity_utilization_pct"]:.2f}',
            f'{item.get("availability_pct", 0.0):.2f}',
            f'{item.get("revenue_loss_from_outages_inr", 0.0):,.2f}',
            f'{item["revenue_inr"]:,.2f}',
            f'{item["operating_cost_inr"]:,.2f}',
            f'{item.get("utility_island_service_cost_inr", 0.0):,.2f}',
            f'{item.get("utility_island_replacement_cost_inr", 0.0):,.2f}',
            f'{item.get("utility_island_turnaround_cost_inr", 0.0):,.2f}',
            f'{item.get("principal_repayment_inr", 0.0):,.2f}',
            f'{item["interest_inr"]:,.2f}',
            f'{item.get("debt_service_inr", 0.0):,.2f}',
            f'{item.get("cfads_inr", 0.0):,.2f}',
            f'{item.get("dscr", 0.0):.3f}',
            f'{item["depreciation_inr"]:,.2f}',
            f'{item["profit_before_tax_inr"]:,.2f}',
            f'{item["tax_inr"]:,.2f}',
            f'{item["profit_after_tax_inr"]:,.2f}',
            f'{item["cash_accrual_inr"]:,.2f}',
        ]
        for item in financial.annual_schedule
    ]
    debt_rows = [
        [
            str(item.year),
            f"{item.opening_debt_inr:,.2f}",
            f"{item.principal_repayment_inr:,.2f}",
            f"{item.interest_inr:,.2f}",
            f"{item.closing_debt_inr:,.2f}",
        ]
        for item in (debt_schedule.entries if debt_schedule else [])
    ]
    financial_schedule_rows = [
        [
            str(item.year),
            f"{item.capacity_utilization_pct:.2f}",
            f"{item.availability_pct:.2f}",
            f"{item.dscr:.3f}",
            f"{item.cfads_inr:,.2f}",
            f"{item.revenue_inr:,.2f}",
            f"{item.operating_cost_inr:,.2f}",
            f"{item.profit_before_tax_inr:,.2f}",
            f"{item.cash_accrual_inr:,.2f}",
        ]
        for item in (financial_schedule.lines if financial_schedule else [])
    ]
    utility_architecture_rows = [
        [
            case.case_id,
            case.base_case_id or "-",
            case.topology,
            case.architecture_family,
            f"{case.recovered_duty_kw:.3f}",
            f"{case.residual_hot_utility_kw:.3f}",
            str(case.header_count),
            str(case.shared_htm_island_count),
            str(case.condenser_reboiler_cluster_count),
            str(case.exchanger_count),
        ]
        for case in (utility_architecture.architecture.cases if utility_architecture else [])
    ]
    utility_train_rows = [
        [
            step.exchanger_id,
            step.island_id or "-",
            step.cluster_id or "-",
            str(step.header_level or 0),
            step.topology,
            step.service,
            step.source_unit_id,
            step.sink_unit_id,
            f"{step.recovered_duty_kw:.3f}",
            step.medium,
        ]
        for step in (utility_architecture.architecture.selected_train_steps if utility_architecture else [])
    ]
    utility_island_rows = [
        [
            island.island_id,
            island.topology,
            island.architecture_role,
            str(island.header_level or 0),
            island.cluster_id or "-",
            ", ".join(island.unit_ids),
            f"{island.target_recovered_duty_kw:.3f}",
            f"{island.recoverable_potential_kw:.3f}",
            f"{island.recovered_duty_kw:.3f}",
            f"{island.residual_hot_utility_kw:.3f}",
            f"{island.residual_cold_utility_kw:.3f}",
            str(island.candidate_match_count),
            str(island.direct_match_count),
            str(island.indirect_match_count),
            f"{island.shared_htm_inventory_m3:.3f}",
            f"{island.header_design_pressure_bar:.2f}",
            f"{island.condenser_reboiler_pair_score:.3f}",
            f"{island.control_complexity_factor:.3f}",
        ]
        for island in (
            next(
                (
                    case.utility_islands
                    for case in utility_architecture.architecture.cases
                    if case.case_id == utility_architecture.architecture.selected_case_id
                ),
                [],
            )
            if utility_architecture
            else []
        )
    ]
    composite_interval_rows = [
        [
            interval.interval_id,
            f"{interval.shifted_upper_temp_c:.1f}",
            f"{interval.shifted_lower_temp_c:.1f}",
            f"{interval.hot_duty_kw:.3f}",
            f"{interval.cold_duty_kw:.3f}",
            f"{interval.net_duty_kw:.3f}",
        ]
        for interval in (
            utility_architecture.architecture.heat_stream_set.composite_intervals
            if utility_architecture and utility_architecture.architecture.heat_stream_set
            else []
        )
    ]
    utility_package_rows = [
        [
            item.island_id or "-",
            item.cluster_id or "-",
            str(item.header_level or 0),
            item.parent_step_id,
            item.equipment_id,
            item.package_role,
            item.package_family,
            item.equipment_type,
            item.service,
            f"{item.design_temperature_c:.1f}",
            f"{item.design_pressure_bar:.2f}",
            f"{item.volume_m3:.3f}",
            f"{item.duty_kw:.3f}",
            f"{item.power_kw:.3f}",
            f"{item.flow_m3_hr:.3f}",
            f"{item.lmtd_k:.3f}",
            f"{item.heat_transfer_area_m2:.3f}",
            f"{item.phase_change_load_kg_hr:.3f}",
        ]
        for item in (utility_architecture.architecture.selected_package_items if utility_architecture else [])
    ]
    agent_packet_rows = [
        [
            packet.packet_id,
            packet.specialist_role,
            packet.option_set.selected_candidate_id or (packet.selected_decision.selected_candidate_id if packet.selected_decision else "-"),
            packet.critic_verdicts[0].status if packet.critic_verdicts else "-",
        ]
        for packet in (agent_fabric.packets if agent_fabric else [])
    ]
    critic_rows = [
        [
            finding.stage_id,
            finding.critic_family,
            finding.severity.value,
            finding.code,
            finding.artifact_ref or "-",
            finding.recommended_action or "-",
        ]
        for finding in (critic_registry.findings if critic_registry else [])
    ]
    rejected_rows: list[list[str]] = []
    for decision in [
        process_synthesis.operating_mode_decision if process_synthesis else None,
        site_decision,
        route_decision,
        utility_basis_decision,
        economic_basis_decision,
        control_architecture.decision if control_architecture else None,
        *extra_decisions,
    ]:
        if decision is None:
            continue
        for alternative in decision.alternatives:
            if alternative.rejected_reasons:
                rejected_rows.append([decision.decision_id, alternative.candidate_id, "; ".join(alternative.rejected_reasons)])
    alternative_set_rows: list[list[str]] = []
    if process_synthesis:
        for alt_set in process_synthesis.alternative_sets:
            for alternative in alt_set.alternatives:
                alternative_set_rows.append(
                    [
                        alt_set.set_id,
                        alternative.candidate_id,
                        alternative.description,
                        f"{alternative.total_score:.2f}",
                        "yes" if alternative.candidate_id == alt_set.selected_candidate_id else "no",
                    ]
                )
    hazop_rows = [
        [node.node_id, node.parameter, node.guide_word, "; ".join(node.safeguards)]
        for node in (hazop_register.nodes if hazop_register else [])
    ]
    datasheet_rows = [
        [item.equipment_id, item.service, f"{item.design_temperature_c:.1f}", f"{item.design_pressure_bar:.2f}", f"{item.volume_m3:.3f}", item.material_of_construction]
        for item in equipment
    ]
    reactor_basis_rows = [
        ["Selected type", reactor_design_basis.selected_reactor_type],
        ["Governing equations", "; ".join(reactor_design_basis.governing_equations)],
        ["Operating envelope", "; ".join(f"{key}={value}" for key, value in reactor_design_basis.operating_envelope.items())],
    ] if reactor_design_basis else []
    column_hydraulics_rows = [
        ["Flooding fraction", f"{column_hydraulics.flooding_fraction:.3f}"],
        ["Tray spacing (m)", f"{column_hydraulics.tray_spacing_m:.3f}"],
        ["Downcomer area fraction", f"{column_hydraulics.downcomer_area_fraction:.3f}"],
        ["Vapor velocity (m/s)", f"{column_hydraulics.vapor_velocity_m_s:.3f}"],
        ["Allowable vapor velocity (m/s)", f"{column_hydraulics.allowable_vapor_velocity_m_s:.3f}"],
        ["Capacity factor (m/s)", f"{column_hydraulics.capacity_factor_m_s:.3f}"],
        ["Active area (m2)", f"{column_hydraulics.active_area_m2:.3f}"],
        ["Liquid load (m3/h)", f"{column_hydraulics.liquid_load_m3_hr:.3f}"],
        ["Pressure drop per stage (kPa)", f"{column_hydraulics.pressure_drop_per_stage_kpa:.3f}"],
    ] if column_hydraulics else []
    exchanger_thermal_rows = [
        ["Configuration", exchanger_thermal.selected_configuration],
        ["Equations", "; ".join(exchanger_thermal.governing_equations)],
        ["Thermal inputs", "; ".join(f"{key}={value}" for key, value in exchanger_thermal.thermal_inputs.items())],
        ["Package basis", "; ".join(f"{key}={value}" for key, value in exchanger_thermal.package_basis.items())],
    ] if exchanger_thermal else []
    pump_rows = [
        ["Pump ID", pump_design.pump_id],
        ["Service", pump_design.service],
        ["Flow (m3/h)", f"{pump_design.flow_m3_hr:.3f}"],
        ["Head (m)", f"{pump_design.differential_head_m:.3f}"],
        ["Power (kW)", f"{pump_design.power_kw:.3f}"],
    ] if pump_design else []

    mechanical_headers = [
        "Equipment",
        "Type",
        "Shell t (mm)",
        "Head t (mm)",
        "Class",
        "Hydrotest (bar)",
        "Nozzle (mm)",
        "Support",
        "Load Case",
        "Support t (mm)",
        "Load (kN)",
        "Wind (kN)",
        "Seismic (kN)",
        "Piping (kN)",
        "Thermal Growth (mm)",
        "Reinforcement (mm2)",
        "Support Variant",
        "Anchor Groups",
        "Footprint (m2)",
        "Clearance (m)",
        "Ladder",
        "Lifting Lugs",
        "Reinf. Family",
        "Shell Factor",
        "Platform",
        "Platform Area (m2)",
    ]
    mechanical_rows_view = mechanical_rows or [["n/a"] * len(mechanical_headers)]
    utility_island_headers = [
        "Island",
        "Topology",
        "Role",
        "Header",
        "Cluster",
        "Units",
        "Target Duty (kW)",
        "Potential (kW)",
        "Recovered Duty (kW)",
        "Residual Hot Utility (kW)",
        "Residual Cold Utility (kW)",
        "Candidates",
        "Direct Matches",
        "Indirect Matches",
        "HTM Inventory (m3)",
        "Header Pressure (bar)",
        "Pair Score",
        "Control Factor",
    ]
    utility_island_rows_view = utility_island_rows or [["n/a"] * len(utility_island_headers)]
    utility_package_headers = [
        "Island",
        "Cluster",
        "Header",
        "Step",
        "Equipment",
        "Role",
        "Family",
        "Type",
        "Service",
        "Design Temp (C)",
        "Design Pressure (bar)",
        "Volume (m3)",
        "Duty (kW)",
        "Power (kW)",
        "Flow (m3/h)",
        "LMTD (K)",
        "Area (m2)",
        "Phase Load (kg/h)",
    ]
    utility_package_rows_view = utility_package_rows or [["n/a"] * len(utility_package_headers)]
    financial_schedule_headers = [
        "Year",
        "Capacity Utilization (%)",
        "Availability (%)",
        "Revenue Loss (INR)",
        "Revenue (INR)",
        "Operating Cost (INR)",
        "Utility-Island Service (INR)",
        "Utility-Island Replacement (INR)",
        "Utility-Island Turnaround (INR)",
        "Principal (INR)",
        "Interest (INR)",
        "Debt Service (INR)",
        "CFADS (INR)",
        "DSCR",
        "Depreciation (INR)",
        "PBT (INR)",
        "Tax (INR)",
        "PAT (INR)",
        "Cash Accrual (INR)",
    ]
    financial_schedule_rows_view = schedule_rows or [["n/a"] * len(financial_schedule_headers)]

    sections = [
        "## Annexures",
        "",
        "### Appendix A: Material Safety Data Sheet",
        "",
        "Screening MSDS-style sheets derived from the selected-route hazard basis, product safety notes, and the report's SHE basis.",
        "",
        "#### Material Safety Data Sheet Summary",
        markdown_table(
            ["Material", "Role", "Formula", "Hazard Summary", "Handling / Storage Basis", "Emergency / PPE Basis"],
            msds_rows,
        ),
        "",
        "### Appendix B: Python Code and Reproducibility Bundle",
        "",
        "#### Core Module Register",
        markdown_table(["Bundle Item", "Path", "Purpose"], appendix_code_rows),
        "",
        "#### Reproducibility Artifact Register",
        markdown_table(["Artifact", "Value / Count", "Purpose"], appendix_artifact_rows),
        "",
        "### Appendix C: Process Design Data Sheet",
        "",
        "#### Process Design Data Sheet Summary",
        markdown_table(["Equipment", "Service", "Design Temp (C)", "Design Pressure (bar)", "Volume (m3)", "MoC"], datasheet_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "#### Process Design Data Sheet Bundle",
        equipment_datasheets_markdown or "No equipment datasheet bundle captured.",
        "",
        "### Benchmark Manifest",
        markdown_table(["Field", "Value"], benchmark_rows or [["n/a", "n/a"]]),
        "",
        "### Source Ranking Table",
        markdown_table(["Domain", "Source ID", "Score", "Selected", "Conflict"], source_resolution_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Source Conflict Register",
        markdown_table(["Domain", "Selected", "Competing", "Score Gap", "Blocking", "Recommended Resolution"], source_conflict_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Property Table",
        markdown_table(["Property", "Value", "Units", "Method", "Sources"], property_rows),
        "",
        "### Component Identifier Table",
        markdown_table(["Identifier", "Canonical Name", "Formula", "CAS", "Route IDs", "Status"], property_identifier_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Pure-Component Property Table",
        markdown_table(["Component", "Property", "Value", "Units", "Ref Temp (C)", "Method", "Status", "Sources"], pure_component_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Property Correlation Register",
        markdown_table(["Identifier", "Property", "Equation", "Parameters", "Tmin (C)", "Tmax (C)", "Method", "Sources"], property_correlation_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Binary Interaction Parameter Register",
        markdown_table(["Component A", "Component B", "Model", "Tau12", "Tau21", "Alpha12", "Status", "Sources"], binary_interaction_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Henry-Law Constant Register",
        markdown_table(["Gas", "Solvent", "Value", "Units", "Ref Temp (C)", "Equation", "Status", "Sources"], henry_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Solubility Curve Register",
        markdown_table(["Solute", "Solvent", "Equation", "Parameters", "Tmin (C)", "Tmax (C)", "Units", "Status", "Sources"], solubility_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Value Provenance Table",
        markdown_table(["Name", "Value", "Units", "Method", "Sensitivity", "Blocking", "Sources"], value_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Resolved Value Table",
        markdown_table(["Name", "Resolution Level", "Status", "Sensitivity", "Selected Source", "Justification"], resolved_value_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Property Estimate Register",
        markdown_table(["Property", "Selected Method", "Candidate Methods", "Selected Source", "Sensitivity", "Blocking"], property_estimate_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Property Requirement Coverage",
        markdown_table(["Stage", "Identifier", "Property", "Status", "Allow Estimated", "Blocking"], requirement_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Separation Thermodynamics Basis",
        markdown_table(["Field", "Value"], separation_thermo_rows or [["n/a", "n/a"]]),
        "",
        "### Component K-Value Register",
        markdown_table(["Component", "Top T (C)", "Top Gamma", "Top K", "Top Method", "Bottom T (C)", "Bottom Gamma", "Bottom K", "Bottom Method"], separation_thermo_component_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Blocked / Unresolved Property Register",
        markdown_table(["Component", "Property", "Package Status", "Blocking"], unresolved_property_rows or [["n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Reaction Extent Set",
        markdown_table(["Extent", "Kind", "Representative Component", "Fraction of Converted Feed", "Status"], reaction_extent_rows or [["n/a", "n/a", "n/a", "0.0", "n/a"]]),
        "",
        "### Byproduct Closure Register",
        markdown_table(["Component", "Basis", "Allocation Fraction", "Provenance", "Status"], byproduct_closure_rows or [["n/a", "n/a", "0.0", "n/a", "n/a"]]),
        "",
        "### Process Archetype",
        markdown_table(["Field", "Value"], archetype_rows or [["n/a", "n/a"]]),
        "",
        "### Route Family Profiles",
        markdown_table(
            ["Route", "Family", "Reactor Basis", "Separation Train", "Heat Style", "Maturity", "India Fit", "Critic Flags", "India Blocker"],
            route_family_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Unit-Operation Family Expansion",
        markdown_table(
            ["Service Group", "Candidate", "Status", "Score", "Description"],
            unit_operation_family_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        markdown_table(["Field", "Value"], unit_operation_support_rows),
        "",
        "### Sparse-Data Policy",
        markdown_table(
            ["Stage", "Subject", "Artifact Family", "Allow Estimated", "Allow Analogy", "Allow Heuristic Fallback", "Min Confidence", "Status", "Triggered Items"],
            sparse_policy_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "0.00", "n/a", "-"]],
        ),
        "",
        "### Operations Planning Basis",
        markdown_table(["Field", "Value"], operations_rows or [["n/a", "n/a"]]),
        "",
        "### Specialist Decision Fabric",
        markdown_table(["Packet", "Specialist", "Selected", "Critic Status"], agent_packet_rows or [["n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Critic Registry",
        markdown_table(["Stage", "Family", "Severity", "Code", "Artifact", "Recommended Action"], critic_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Alternative Set Summary",
        markdown_table(["Set", "Candidate", "Description", "Score", "Selected"], alternative_set_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Stream Table",
        markdown_table(["Stream", "Description", "Component", "kg/h", "kmol/h"], stream_rows),
        "",
        "### Flowsheet Graph",
        markdown_table(["Node", "Unit Type", "Upstream", "Downstream", "Representative Streams"], flowsheet_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Flowsheet Case",
        markdown_table(
            ["Unit", "Type", "Inlet Streams", "Outlet Streams", "Closure Status", "Coverage", "Unresolved Sensitivities"],
            flowsheet_case_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Unit Composition States",
        markdown_table(
            ["Unit", "Type", "Inlet Phase", "Outlet Phase", "Top Outlet Components", "Status"],
            composition_state_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Composition Closures",
        markdown_table(
            ["Unit", "Reactive", "Inlet Fraction Sum", "Outlet Fraction Sum", "Composition Error (%)", "Status"],
            composition_closure_rows or [["n/a", "n/a", "0", "0", "0", "n/a"]],
        ),
        "",
        "### Mixture Property Packages",
        markdown_table(
            ["Unit", "Phase", "Cp (kJ/kg-K)", "Density (kg/m3)", "Viscosity (Pa.s)", "Status", "Estimated Properties"],
            mixture_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Solve Result",
        markdown_table(
            ["Unit", "Closure Error (%)", "Solve Status", "Coverage", "Unresolved Sensitivities"],
            solve_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Phase Split Specs",
        markdown_table(
            ["Unit", "Family", "Mechanism", "Inlet Phases", "Product Phase", "Waste Phase", "Recycle Phase", "Status"],
            phase_split_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Separator Performance",
        markdown_table(
            ["Unit", "Family", "Status", "Product Mass Frac", "Waste Mass Frac", "Recycle Mass Frac", "Split Closure (%)"],
            separator_performance_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]],
        ),
        "",
        "### Recycle Convergence Summaries",
        markdown_table(
            ["Loop", "Source Unit", "Status", "Max Component Error (%)", "Mean Component Error (%)", "Max Iterations", "Purge Policy"],
            recycle_convergence_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "-"]],
        ),
        "",
        "### Equipment Table",
        markdown_table(["ID", "Type", "Service", "Volume (m3)", "Design Temp (C)", "Design Pressure (bar)", "MoC"], equipment_rows),
        "",
        _narrow_table_section(
            "Mechanical Design Summary View",
            mechanical_headers,
            mechanical_rows_view,
            ["Equipment", "Type", "Shell t (mm)", "Head t (mm)", "Class", "Support", "Load Case", "Platform"],
        ),
        "",
        _narrow_table_section(
            "Mechanical Load and Foundation View",
            mechanical_headers,
            mechanical_rows_view,
            ["Equipment", "Load (kN)", "Wind (kN)", "Seismic (kN)", "Piping (kN)", "Anchor Groups", "Footprint (m2)", "Clearance (m)"],
        ),
        "",
        "### Mechanical Design Table",
        markdown_table(mechanical_headers, mechanical_rows_view),
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
                ["Peak Working Capital", f"INR {financial.peak_working_capital_inr:,.2f}"],
                ["Peak Working-Capital Month", f"{financial.peak_working_capital_month:.2f}"],
                ["Total Import Duty", f"INR {cost_model.total_import_duty_inr:,.2f}"],
                ["IDC", f"{financial.currency} {financial.construction_interest_during_construction_inr:,.2f}"],
                ["Minimum DSCR", f"{financial.minimum_dscr:.3f}"],
                ["Average DSCR", f"{financial.average_dscr:.3f}"],
                ["LLCR", f"{financial.llcr:.3f}"],
                ["PLCR", f"{financial.plcr:.3f}"],
                ["Selected Financing Option", financial.selected_financing_candidate_id or "n/a"],
                ["Downside Scenario", financial.downside_scenario_name or "n/a"],
                ["Downside-Preferred Financing Option", financial.downside_financing_candidate_id or "n/a"],
                ["Scenario Reversal", "yes" if financial.financing_scenario_reversal else "no"],
                ["Covenant Breaches", ", ".join(financial.covenant_breach_codes) or "none"],
                ["Payback (y)", f"{financial.payback_years:.3f}"],
                ["NPV", f"{financial.currency} {financial.npv:,.2f}"],
                ["IRR (%)", f"{financial.irr:.2f}"],
            ],
        ),
        "",
        "### Lender Coverage Screening",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Minimum DSCR", f"{financial.minimum_dscr:.3f}"],
                ["Average DSCR", f"{financial.average_dscr:.3f}"],
                ["LLCR", f"{financial.llcr:.3f}"],
                ["PLCR", f"{financial.plcr:.3f}"],
                ["Downside Scenario", financial.downside_scenario_name or "n/a"],
                ["Downside-Preferred Financing Option", financial.downside_financing_candidate_id or "n/a"],
                ["Scenario Reversal", "yes" if financial.financing_scenario_reversal else "no"],
            ],
        ),
        "",
        "### Covenant Warnings",
        ("\n".join(f"- {warning}" for warning in financial.covenant_warnings) if financial.covenant_warnings else "- No covenant warnings under the current screening basis."),
        "",
        "### Equipment Cost Breakdown",
        markdown_table(["Equipment", "Type", "Bare Cost (INR)", "Installed Cost (INR)", "Spares (INR)", "Package Family", "Lead (mo)", "Import Duty (INR)", "Basis"], equipment_cost_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Plant Cost Summary",
        markdown_table(["Equipment", "Bare", "Installation", "Piping", "Instrumentation", "Total Installed"], plant_cost_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Procurement Timing Schedule",
        markdown_table(["Package Family", "Milestone", "Month", "Draw Fraction", "CAPEX Draw (INR)"], procurement_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Procurement Package Detail",
        markdown_table(["Equipment", "Type", "Package Family", "Lead (mo)", "Award Month", "Delivery Month", "Import Content", "Duty Fraction", "Import Duty (INR)", "CAPEX Burden (INR)"], procurement_package_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Working-Capital Timing Basis",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Procurement Timing Factor", f"{working_capital.procurement_timing_factor:.3f}"],
                ["Pre-commissioning Inventory Days", f"{working_capital.precommissioning_inventory_days:.2f}"],
                ["Pre-commissioning Inventory Month", f"{working_capital.precommissioning_inventory_month:.2f}"],
                ["Pre-commissioning Inventory", f"INR {working_capital.precommissioning_inventory_inr:,.2f}"],
                ["Peak Working-Capital Month", f"{working_capital.peak_working_capital_month:.2f}"],
                ["Peak Working Capital", f"INR {working_capital.peak_working_capital_inr:,.2f}"],
            ],
        ),
        "",
        "### Mechanical Screening Table",
        markdown_table(
            [
                "Equipment",
                "Type",
                "Shell t (mm)",
                "Head t (mm)",
                "Class",
                "Hydrotest (bar)",
                "Nozzle (mm)",
                "Support",
                "Load Case",
                "Support t (mm)",
                "Load (kN)",
                "Wind (kN)",
                "Seismic (kN)",
                "Piping (kN)",
                "Thermal Growth (mm)",
                "Reinforcement (mm2)",
                "Support Variant",
                "Anchor Groups",
                "Footprint (m2)",
                "Clearance (m)",
                "Ladder",
                "Lifting Lugs",
                "Reinf. Family",
                "Shell Factor",
                "Platform",
                "Platform Area (m2)",
            ],
            mechanical_rows
            or [["n/a"] * 26],
        ),
        "",
        "### Utility Island Economics",
        markdown_table(["Island", "Topology", "HTM Inventory (m3)", "Header Pressure (bar)", "Pair Score", "Control Factor", "Cycle (y)", "Replacement Event (INR)", "Replacement Avg (INR/y)", "Turnaround (d)", "Project CAPEX Burden (INR)", "Allocated Utility (INR/y)", "Service (INR/y)", "Operating Burden (INR/y)", "Utility Share", "CAPEX Share"], utility_island_economic_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Utility Island Scenario Breakdown",
        markdown_table(["Scenario", "Island", "Capex Burden (INR)", "Allocated Utility (INR/y)", "Service (INR/y)", "Replacement (INR/y)", "Operating Burden (INR/y)"], utility_island_scenario_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Scenario Comparison Table",
        markdown_table(["Scenario", "Utility Cost (INR/y)", "Transport/Service (INR/y)", "Utility-Island Burden (INR/y)", "Operating Cost (INR/y)", "Revenue (INR/y)", "Gross Margin (INR/y)"], scenario_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Multi-Year Financial Schedule",
        _narrow_table_section(
            "Financial Schedule Summary View",
            financial_schedule_headers,
            financial_schedule_rows_view,
            ["Year", "Capacity Utilization (%)", "Availability (%)", "Revenue (INR)", "Operating Cost (INR)", "CFADS (INR)", "DSCR", "Cash Accrual (INR)"],
        ),
        "",
        _narrow_table_section(
            "Financial Schedule Debt and Profit View",
            financial_schedule_headers,
            financial_schedule_rows_view,
            ["Year", "Principal (INR)", "Interest (INR)", "Debt Service (INR)", "PBT (INR)", "Tax (INR)", "PAT (INR)"],
        ),
        "",
        markdown_table(financial_schedule_headers, financial_schedule_rows_view),
        "",
        "### Typed Financial Schedule",
        markdown_table(["Year", "Capacity Utilization (%)", "Availability (%)", "DSCR", "CFADS", "Revenue", "Opex", "PBT", "Cash Accrual"], financial_schedule_rows or [["n/a"] * 9]),
        "",
        "### Debt Schedule",
        markdown_table(["Year", "Opening Debt", "Principal", "Interest", "Closing Debt"], debt_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Heat Integration Cases",
        markdown_table(["Route", "Case ID", "Title", "Recovered Duty (kW)", "Residual Hot Utility (kW)", "Annual Savings (INR)", "Payback (y)", "Feasible"], heat_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Utility Architecture",
        markdown_table(["Case", "Base Case", "Topology", "Family", "Recovered Duty (kW)", "Residual Hot Utility (kW)", "Header Levels", "Shared HTM Islands", "Cond-Reb Clusters", "Exchanger Count"], utility_architecture_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Composite Thermal Intervals",
        markdown_table(["Interval", "Shifted Upper (C)", "Shifted Lower (C)", "Hot Duty (kW)", "Cold Duty (kW)", "Net Duty (kW)"], composite_interval_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Utility Islands",
        _narrow_table_section(
            "Utility Island Summary View",
            utility_island_headers,
            utility_island_rows_view,
            ["Island", "Topology", "Role", "Header", "Units", "Target Duty (kW)", "Recovered Duty (kW)", "Residual Hot Utility (kW)"],
        ),
        "",
        _narrow_table_section(
            "Utility Island Operating Window View",
            utility_island_headers,
            utility_island_rows_view,
            ["Island", "Candidates", "Direct Matches", "Indirect Matches", "HTM Inventory (m3)", "Header Pressure (bar)", "Pair Score", "Control Factor"],
        ),
        "",
        markdown_table(utility_island_headers, utility_island_rows_view),
        "",
        "### Selected Utility Train",
        markdown_table(["Exchanger", "Island", "Cluster", "Header", "Topology", "Service", "Hot Unit", "Cold Unit", "Recovered Duty (kW)", "Medium"], utility_train_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Utility Train Packages",
        _narrow_table_section(
            "Utility Train Package Summary View",
            utility_package_headers,
            utility_package_rows_view,
            ["Equipment", "Role", "Family", "Type", "Service", "Design Temp (C)", "Design Pressure (bar)", "Duty (kW)", "Area (m2)"],
        ),
        "",
        _narrow_table_section(
            "Utility Train Package Hydraulic View",
            utility_package_headers,
            utility_package_rows_view,
            ["Equipment", "Header", "Volume (m3)", "Power (kW)", "Flow (m3/h)", "LMTD (K)", "Phase Load (kg/h)"],
        ),
        "",
        markdown_table(utility_package_headers, utility_package_rows_view),
        "",
        _decision_markdown("Operating Mode Decision", process_synthesis.operating_mode_decision if process_synthesis else None),
        "",
        _decision_markdown("Control Architecture Decision", control_architecture.decision if control_architecture else None),
        "",
        _decision_markdown("Site Decision", site_decision),
        "",
        _decision_markdown("Route Decision", route_decision),
        "",
        _decision_markdown("Utility Basis Decision", utility_basis_decision),
        "",
        _decision_markdown("Economic Basis Decision", economic_basis_decision),
        "",
        *[
            section
            for decision in extra_decisions
            for section in ["", _decision_markdown(decision.decision_id.replace("_", " ").title(), decision)]
        ],
        "",
        "### HAZOP Node Register",
        markdown_table(["Node", "Parameter", "Guide Word", "Safeguards"], hazop_rows or [["n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Rejected Alternative Log",
        markdown_table(["Decision", "Candidate", "Reasons"], rejected_rows or [["n/a", "n/a", "n/a"]]),
        "",
        "### Economic Scenario Model",
        economic_scenarios.markdown if economic_scenarios else "No economic scenario model captured.",
        "",
        "### Reactor Design Basis",
        markdown_table(["Field", "Value"], reactor_basis_rows or [["n/a", "n/a"]]),
        "",
        "### Column Hydraulics",
        markdown_table(["Field", "Value"], column_hydraulics_rows or [["n/a", "n/a"]]),
        "",
        "### Heat Exchanger Thermal Design",
        markdown_table(["Field", "Value"], exchanger_thermal_rows or [["n/a", "n/a"]]),
        "",
        "### Pump Design",
        markdown_table(["Field", "Value"], pump_rows or [["n/a", "n/a"]]),
        "",
        "### Mechanical Design Basis",
        markdown_table(
            ["Field", "Value"],
            [
                ["Code basis", mechanical_design_basis.code_basis],
                ["Design pressure basis", mechanical_design_basis.design_pressure_basis],
                ["Design temperature basis", mechanical_design_basis.design_temperature_basis],
                ["Corrosion allowance (mm)", f"{mechanical_design_basis.corrosion_allowance_mm:.2f}"],
                ["Support design basis", mechanical_design_basis.support_design_basis],
                ["Load case basis", mechanical_design_basis.load_case_basis],
                ["Foundation basis", mechanical_design_basis.foundation_basis],
                ["Nozzle load basis", mechanical_design_basis.nozzle_load_basis],
                ["Connection rating basis", mechanical_design_basis.connection_rating_basis],
                ["Access platform basis", mechanical_design_basis.access_platform_basis],
            ] if mechanical_design_basis else [["n/a", "n/a"]],
        ),
        "",
        "### Tax and Depreciation Basis",
        tax_depreciation_basis.markdown if tax_depreciation_basis else "No tax/depreciation basis captured.",
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
    toc_lines = ["- List of Tables", "- List of Figures", ""]
    toc_lines.extend(f"{index}. {chapter.title}" for index, chapter in enumerate(ordered, start=1))
    references_number = len(ordered) + 1
    appendices_number = len(ordered) + 2
    index_rows = [[str(index), chapter.title, str(index)] for index, chapter in enumerate(ordered, start=1)]
    appendix_index_rows = [
        ["A", "Material Safety Data Sheet", "Appendix A"],
        ["B", "Python Code and Reproducibility Bundle", "Appendix B"],
        ["C", "Process Design Data Sheet", "Appendix C"],
    ]
    toc_lines.extend(
        [
            f"{references_number}. References",
            f"{appendices_number}. Appendices and Annexures",
            "   - Appendix A: Material Safety Data Sheet",
            "   - Appendix B: Python Code and Reproducibility Bundle",
            "   - Appendix C: Process Design Data Sheet",
        ]
    )
    basis_rows = [
        ["Target product", project_basis.target_product],
        ["Capacity", f"{project_basis.capacity_tpa:.2f} TPA"],
        ["Purity target", f"{project_basis.target_purity_wt_pct:.2f} wt%"],
        ["Operating mode", project_basis.operating_mode],
        ["Region", project_basis.region],
        ["Currency", project_basis.currency],
        ["Process template", project_basis.process_template.value],
    ]
    control_rows = [
        ["Report type", "End-to-end techno-economic feasibility and plant design report"],
        ["Issue date", date.today().isoformat()],
        ["Report basis", "Solver-backed benchmark-parity report package"],
        ["Document coverage", "Chapters, references, appendices, annexures, and datasheet bundle"],
    ]
    formatted_annexures = _format_appendix_bundle(_strip_leading_heading(annexures_md, "## Annexures"))
    body = [
        f"# {project_basis.target_product} Plant Design Report",
        "",
        "## Preliminary Techno-Economic Feasibility Report",
        "",
        f"**Target product:** {project_basis.target_product}",
        "",
        f"**Design capacity:** {project_basis.capacity_tpa:.2f} TPA",
        "",
        f"**Region:** {project_basis.region}",
        "",
        f"**Issue date:** {date.today().isoformat()}",
        "",
        "---",
        "",
        "## Report Basis",
        "",
        markdown_table(["Field", "Value"], basis_rows),
        "",
        "## Document Control",
        "",
        markdown_table(["Field", "Value"], control_rows),
        "",
        "## Table of Contents",
        "\n".join(toc_lines),
        "",
        "## Index",
        "",
        markdown_table(["Sr. No.", "Content", "Section"], index_rows),
        "",
        "## Appendix Index",
        "",
        markdown_table(["Appendix", "Content", "Section"], appendix_index_rows),
        "",
    ]
    for index, chapter in enumerate(ordered, start=1):
        if index > 1:
            body.extend(["---", ""])
        body.append(f"# {index}. {chapter.title}")
        body.append("")
        body.append(chapter.rendered_markdown.strip())
        body.append("")
    body.extend(
        [
            "---",
            "",
            f"# {references_number}. References",
            "",
            _strip_leading_heading(references_md, "## References"),
            "",
            "---",
            "",
            f"# {appendices_number}. Appendices and Annexures",
            "",
            formatted_annexures,
            "",
        ]
    )
    captioned_report = _apply_caption_numbering("\n".join(body).strip())
    register_sections = _build_caption_register_sections(captioned_report)
    if ordered:
        first_chapter_heading = f"# 1. {ordered[0].title}"
        captioned_report = captioned_report.replace(f"\n{first_chapter_heading}", f"\n{register_sections}\n\n{first_chapter_heading}", 1)
    else:
        captioned_report = "\n".join([captioned_report, "", register_sections]).strip()
    return captioned_report + "\n"


def render_pdf(markdown_text: str, output_path: str, title: str) -> str:
    clean_text = re.sub(r"`", "", markdown_text)
    clean_text = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_text)
    clean_text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", clean_text)
    document = fitz.open()
    page_headers: list[str | None] = []
    page = None
    y = 48
    clean_lines = clean_text.splitlines()
    current_header: str | None = None

    def create_page(header_text: str | None = None, top_y: float | None = None) -> None:
        nonlocal page, y
        page = document.new_page()
        page.set_mediabox(fitz.Rect(0, 0, 595, 842))
        page_headers.append(header_text)
        y = 48 if top_y is None else top_y

    create_page()

    def ensure_space(required_bottom: float = 790) -> None:
        nonlocal page, y
        if y > required_bottom:
            create_page(current_header, top_y=60 if current_header else 48)

    def render_wrapped(text: str, fontsize: int = 10, line_spacing: int = 12, wrap_width: int = 92, indent: int = 0) -> None:
        nonlocal y
        wrapped = textwrap.wrap(text, width=wrap_width) or [text]
        for line in wrapped:
            ensure_space()
            page.insert_text((48 + indent, y), line, fontsize=fontsize, fontname="helv")
            y += line_spacing

    index = 0
    while index < len(clean_lines):
        paragraph = clean_lines[index]
        stripped = paragraph.strip()
        if not stripped:
            y += 8
            index += 1
            continue
        if stripped == "---":
            ensure_space()
            page.draw_line(fitz.Point(48, y), fitz.Point(547, y), color=(0, 0, 0), width=0.5)
            y += 10
            index += 1
            continue
        if _is_markdown_table_start(clean_lines, index):
            headers = [cell.strip() for cell in clean_lines[index].strip().strip("|").split("|")]
            render_wrapped("Columns: " + "; ".join(headers), fontsize=9, line_spacing=11, wrap_width=76)
            index += 2
            row_number = 1
            while index < len(clean_lines) and clean_lines[index].strip().startswith("|"):
                values = [cell.strip() for cell in clean_lines[index].strip().strip("|").split("|")]
                row_pairs = [
                    (headers[cell_index] if cell_index < len(headers) else f"Field {cell_index + 1}", values[cell_index] if cell_index < len(values) else "-")
                    for cell_index in range(max(len(headers), len(values)))
                ]
                if len(headers) > 6:
                    render_wrapped(f"Row {row_number}", fontsize=9, line_spacing=11, wrap_width=84)
                    for header, value in row_pairs:
                        render_wrapped(f"{header}: {value}", fontsize=9, line_spacing=10, wrap_width=74, indent=12)
                else:
                    render_wrapped(
                        f"Row {row_number}: " + " | ".join(f"{header}: {value}" for header, value in row_pairs),
                        fontsize=9,
                        line_spacing=10,
                        wrap_width=74,
                    )
                row_number += 1
                index += 1
            y += 4
            continue
        level = 0
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            stripped = stripped.lstrip("#").strip()
        if level == 1 or stripped.startswith("Appendix "):
            current_header = stripped
        if (level == 1 or stripped.startswith("Appendix ")) and y > 80:
            create_page(current_header, top_y=60 if current_header else 48)
        fontsize = 10
        wrap_width = 92
        line_spacing = 12
        if level == 1:
            fontsize = 16
            wrap_width = 62
            line_spacing = 18
        elif level == 2:
            fontsize = 13
            wrap_width = 72
            line_spacing = 15
        elif level == 3:
            fontsize = 11
            wrap_width = 84
            line_spacing = 13
        render_wrapped(stripped, fontsize=fontsize, line_spacing=line_spacing, wrap_width=wrap_width)
        y += 4 if level else 2
        index += 1
    for page_index in range(document.page_count):
        pdf_page = document[page_index]
        header_text = page_headers[page_index] if page_index < len(page_headers) else None
        if header_text:
            pdf_page.insert_text((48, 24), f"{title} | {header_text}", fontsize=8, fontname="helv")
            pdf_page.draw_line(fitz.Point(48, 32), fitz.Point(547, 32), color=(0, 0, 0), width=0.4)
            pdf_page.draw_line(fitz.Point(48, 808), fitz.Point(547, 808), color=(0, 0, 0), width=0.4)
        pdf_page.insert_text((260, 820), f"Page {page_index + 1}", fontsize=9, fontname="helv")
    document.set_metadata({"title": title})
    document.save(output_path)
    document.close()
    return output_path


def render_styled_pdf(html_text: str, output_path: str, title: str, header_text: str | None = None) -> str:
    writer = fitz.DocumentWriter(output_path)
    head_html, body_html = _split_html_head_body(html_text)
    for mode, fragment in _styled_pdf_fragments(body_html):
        story = fitz.Story(html=_wrap_html_fragment(head_html, _normalize_story_fragment(fragment)))
        if mode == "landscape":
            page_rect = fitz.Rect(0, 0, 842, 595)
            content_rect = fitz.Rect(28, 26, 814, 565)
        else:
            page_rect = fitz.Rect(0, 0, 595, 842)
            content_rect = fitz.Rect(54, 54, 541, 790)
        more = True
        page_guard = 0
        while more:
            device = writer.begin_page(page_rect)
            more, _ = story.place(content_rect)
            story.draw(device)
            writer.end_page()
            page_guard += 1
            if page_guard > 250:
                raise RuntimeError(f"Styled PDF fragment exceeded pagination guard for {mode} fragment.")
    writer.close()

    document = fitz.open(output_path)
    for page_index, page in enumerate(document, start=1):
        width = page.rect.width
        height = page.rect.height
        left_margin = 54 if width < 700 else 40
        right_margin = width - left_margin
        if page_index > 1:
            page.insert_text((left_margin, 26), header_text or title, fontsize=8.5, fontname="helv")
            page.draw_line(fitz.Point(left_margin, 32), fitz.Point(right_margin, 32), color=(0, 0, 0), width=0.4)
            page.draw_line(fitz.Point(left_margin, height - 34), fitz.Point(right_margin, height - 34), color=(0, 0, 0), width=0.4)
        page.insert_text((width / 2 - 4, height - 22), str(page_index), fontsize=9, fontname="Times-Roman")
    document.set_metadata({"title": title})
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(temp_fd)
    document.save(temp_path)
    document.close()
    os.replace(temp_path, output_path)
    return output_path


def _split_html_head_body(html_text: str) -> tuple[str, str]:
    head_match = re.search(r"<head>(.*?)</head>", html_text, flags=re.S | re.I)
    body_match = re.search(r"<body>(.*?)</body>", html_text, flags=re.S | re.I)
    head_html = head_match.group(1) if head_match else ""
    body_html = body_match.group(1) if body_match else html_text
    return head_html, body_html


def _wrap_html_fragment(head_html: str, body_fragment: str) -> str:
    return f"<html><head>{head_html}</head><body>{body_fragment}</body></html>"


def _normalize_story_fragment(fragment_html: str) -> str:
    fragment_html = re.sub(r"<diagram-sheet\b([^>]*)>", r"<div class='diagram-sheet'\1>", fragment_html, flags=re.I)
    fragment_html = re.sub(r"</diagram-sheet>", "</div>", fragment_html, flags=re.I)
    return fragment_html


def _styled_pdf_fragments(body_html: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(<diagram-sheet\b[^>]*>.*?</diagram-sheet>)", flags=re.S | re.I)
    parts = re.split(pattern, body_html)
    fragments: list[tuple[str, str]] = []
    for part in parts:
        if not part or not part.strip():
            continue
        stripped = part.lstrip()
        if stripped.lower().startswith("<diagram-sheet"):
            fragments.append(("landscape", part))
        else:
            fragments.extend(("portrait", chunk) for chunk in _split_portrait_fragment(part))
    return fragments


def _split_portrait_fragment(fragment_html: str) -> list[str]:
    chapter_pattern = re.compile(r"(<section class='chapter'>.*?</section>)", flags=re.S)
    parts = re.split(chapter_pattern, fragment_html)
    chunks: list[str] = []
    for part in parts:
        if not part or not part.strip():
            continue
        stripped = part.strip()
        if stripped.startswith("<section class='chapter'>"):
            chunks.append(part)
            continue
        chunks.extend(_split_portrait_supporting_block(part))
    return chunks or [fragment_html]


def _split_portrait_supporting_block(fragment_html: str) -> list[str]:
    heading_pattern = re.compile(r"(?=<h1\b)|(?=<h2\b)")
    parts = re.split(heading_pattern, fragment_html)
    chunks = [part for part in parts if part.strip()]
    return chunks or [fragment_html]


def render_academic_pdf(markdown_text: str, output_path: str, title: str, header_text: str | None = None) -> str:
    clean_text = re.sub(r"`", "", markdown_text)
    clean_text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", clean_text)
    document = fitz.open()
    page_headers: list[str | None] = []
    page = None
    y = 84
    clean_lines = clean_text.splitlines()
    current_header: str | None = None
    cover_mode = True
    left_margin = 62
    right_margin = 533
    page_top = 92
    page_bottom = 778

    def create_page(header_text_value: str | None = None, top_y: float | None = None) -> None:
        nonlocal page, y
        page = document.new_page()
        page.set_mediabox(fitz.Rect(0, 0, 595, 842))
        page_headers.append(header_text_value)
        y = page_top if top_y is None else top_y

    def draw_cover_frame() -> None:
        page.draw_rect(fitz.Rect(48, 48, 547, 794), color=(0, 0, 0), width=1.0)
        page.draw_rect(fitz.Rect(58, 58, 537, 784), color=(0, 0, 0), width=0.4)

    create_page(top_y=110)
    draw_cover_frame()

    def ensure_space(required_bottom: float = page_bottom) -> None:
        nonlocal y
        if y > required_bottom:
            create_page(current_header, top_y=page_top)

    def render_wrapped(
        text: str,
        *,
        fontsize: float = 12,
        line_spacing: float = 14,
        wrap_width: int = 88,
        indent: int = 0,
        fontname: str = "Times-Roman",
        center: bool = False,
    ) -> None:
        nonlocal y
        wrapped = textwrap.wrap(text, width=wrap_width) or [text]
        for line in wrapped:
            ensure_space()
            if center:
                text_width = fitz.get_text_length(line, fontname=fontname, fontsize=fontsize)
                x = max(36, (595 - text_width) / 2)
            else:
                x = left_margin + indent
            page.insert_text((x, y), line, fontsize=fontsize, fontname=fontname)
            y += line_spacing

    def render_chapter_opening(text: str) -> None:
        nonlocal y
        match = re.match(r"Chapter\s+(\d+)\s*:\s*(.*)", text, flags=re.IGNORECASE)
        page.draw_line(fitz.Point(left_margin, y), fitz.Point(right_margin, y), color=(0, 0, 0), width=0.8)
        y += 18
        if match:
            render_wrapped(f"CHAPTER {match.group(1)}", fontsize=11, line_spacing=12, wrap_width=30, fontname="Helvetica")
            render_wrapped(match.group(2).strip().upper(), fontsize=20, line_spacing=24, wrap_width=34, fontname="Times-Bold")
        else:
            render_wrapped(text.upper(), fontsize=18, line_spacing=22, wrap_width=36, fontname="Times-Bold")
        y += 6
        page.draw_line(fitz.Point(left_margin, y), fitz.Point(right_margin), color=(0, 0, 0), width=0.35)
        y += 16

    def render_major_section(text: str) -> None:
        nonlocal y
        render_wrapped(text, fontsize=16, line_spacing=18, wrap_width=42, fontname="Times-Bold")
        y += 2
        page.draw_line(fitz.Point(left_margin, y), fitz.Point(right_margin - 130, y), color=(0, 0, 0), width=0.35)
        y += 12

    index = 0
    while index < len(clean_lines):
        raw_line = clean_lines[index]
        stripped = raw_line.strip()
        if not stripped:
            y += 8
            index += 1
            continue
        if stripped == "---":
            if cover_mode:
                cover_mode = False
                create_page(top_y=page_top)
            else:
                ensure_space()
                page.draw_line(fitz.Point(left_margin, y), fitz.Point(right_margin, y), color=(0, 0, 0), width=0.35)
                y += 10
            index += 1
            continue
        if _is_markdown_table_start(clean_lines, index):
            ensure_space(required_bottom=page_bottom - 40)
            headers = [cell.strip() for cell in clean_lines[index].strip().strip("|").split("|")]
            render_wrapped(" | ".join(headers), fontsize=10.5, line_spacing=12, wrap_width=84, fontname="Helvetica-Bold")
            index += 2
            while index < len(clean_lines) and clean_lines[index].strip().startswith("|"):
                values = [cell.strip() for cell in clean_lines[index].strip().strip("|").split("|")]
                pairs = [
                    f"{headers[cell_index] if cell_index < len(headers) else f'Field {cell_index + 1}'}: {values[cell_index] if cell_index < len(values) else '-'}"
                    for cell_index in range(max(len(headers), len(values)))
                ]
                render_wrapped(" ; ".join(pairs), fontsize=10, line_spacing=11, wrap_width=82, fontname="Times-Roman")
                index += 1
            y += 4
            continue
        level = 0
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            stripped = stripped.lstrip("#").strip()
        if level == 1 or stripped.startswith("Appendix "):
            current_header = stripped
        major_section_headings = {"Executive Summary", "Contents", "List of Tables", "List of Figures", "References", "Appendices"}
        if not cover_mode and (stripped.startswith("Chapter ") or stripped in major_section_headings or stripped.startswith("Appendix ")):
            if y > 110:
                create_page(current_header, top_y=page_top)
        if cover_mode:
            if level == 1:
                render_wrapped(stripped.upper(), fontsize=26, line_spacing=32, wrap_width=24, fontname="Times-Bold", center=True)
            elif level == 2:
                y += 8
                render_wrapped(stripped, fontsize=15, line_spacing=20, wrap_width=42, fontname="Times-Bold", center=True)
            else:
                if stripped.startswith("Prepared for"):
                    y += 44
                render_wrapped(stripped, fontsize=12, line_spacing=15, wrap_width=54, fontname="Times-Roman", center=True)
            y += 6
            index += 1
            continue
        fontsize = 12
        wrap_width = 88
        line_spacing = 14
        fontname = "Times-Roman"
        if level == 1:
            if stripped.startswith("Chapter "):
                render_chapter_opening(stripped)
                index += 1
                continue
            render_major_section(stripped)
            index += 1
            continue
        elif level == 2:
            fontsize = 13.5
            wrap_width = 72
            line_spacing = 17
            fontname = "Times-Bold"
        elif level == 3:
            fontsize = 12
            wrap_width = 82
            line_spacing = 14
            fontname = "Helvetica-Bold"
        render_wrapped(stripped, fontsize=fontsize, line_spacing=line_spacing, wrap_width=wrap_width, fontname=fontname)
        y += 4 if level else 2
        index += 1

    for page_index in range(document.page_count):
        pdf_page = document[page_index]
        if page_index == 0:
            pdf_page.insert_text((190, 736), "PRELIMINARY TECHNO-ECONOMIC FEASIBILITY REPORT", fontsize=10, fontname="Helvetica")
            pdf_page.insert_text((255, 758), date.today().isoformat(), fontsize=10, fontname="Times-Roman")
            continue
        header_value = page_headers[page_index] if page_index < len(page_headers) else None
        pdf_page.insert_text((left_margin, 28), header_text or title, fontsize=8.2, fontname="Helvetica")
        if header_value:
            short_header = re.sub(r"^Chapter\s+\d+\s*:\s*", "", header_value)
            pdf_page.insert_text((390, 28), short_header[:26], fontsize=8.2, fontname="Times-Italic")
        pdf_page.draw_line(fitz.Point(left_margin, 34), fitz.Point(right_margin, 34), color=(0, 0, 0), width=0.35)
        pdf_page.draw_line(fitz.Point(left_margin, 806), fitz.Point(right_margin, 806), color=(0, 0, 0), width=0.35)
        pdf_page.insert_text((285, 822), f"{page_index + 1}", fontsize=9.5, fontname="Times-Roman")
    document.set_metadata({"title": title})
    document.save(output_path)
    document.close()
    return output_path
