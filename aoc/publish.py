from __future__ import annotations

import re
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
    SolveResult,
    SourceRecord,
    StreamTable,
    TaxDepreciationBasis,
    UtilitySummaryArtifact,
    UtilityArchitectureDecision,
    UtilityNetworkDecision,
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
    benchmark_manifest: BenchmarkManifest | None,
    resolved_sources: ResolvedSourceSet | None,
    product_profile: ProductProfileArtifact,
    reaction_system: ReactionSystem | None,
    property_gap: PropertyGapArtifact | None,
    resolved_values: ResolvedValueArtifact | None,
    property_packages: PropertyPackageArtifact | None,
    property_requirements: PropertyRequirementSet | None,
    separation_thermo: SeparationThermoArtifact | None,
    process_archetype: ProcessArchetype | None,
    process_synthesis: ProcessSynthesisArtifact | None,
    agent_fabric: AgentDecisionFabricArtifact | None,
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
            f"{item.nozzle_diameter_mm:.1f}",
            item.support_type,
            f"{item.support_thickness_mm:.2f}",
            f"{item.operating_load_kn:.2f}",
            f"{item.thermal_growth_mm:.2f}",
            f"{item.nozzle_reinforcement_area_mm2:.1f}",
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
        [item.scenario_name, f"{item.annual_utility_cost_inr:,.2f}", f"{item.annual_operating_cost_inr:,.2f}", f"{item.annual_revenue_inr:,.2f}", f"{item.gross_margin_inr:,.2f}"]
        for item in cost_model.scenario_results
    ]
    equipment_cost_rows = [
        [item.equipment_id, item.equipment_type, f"{item.bare_cost_inr:,.2f}", f"{item.installed_cost_inr:,.2f}", f"{item.spares_cost_inr:,.2f}", item.basis]
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
    schedule_rows = [
        [
            str(item["year"]),
            f'{item["capacity_utilization_pct"]:.2f}',
            f'{item["revenue_inr"]:,.2f}',
            f'{item["operating_cost_inr"]:,.2f}',
            f'{item["interest_inr"]:,.2f}',
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
            case.topology,
            f"{case.recovered_duty_kw:.3f}",
            f"{case.residual_hot_utility_kw:.3f}",
            str(case.exchanger_count),
        ]
        for case in (utility_architecture.architecture.cases if utility_architecture else [])
    ]
    utility_train_rows = [
        [
            step.exchanger_id,
            step.topology,
            step.service,
            step.source_unit_id,
            step.sink_unit_id,
            f"{step.recovered_duty_kw:.3f}",
            step.medium,
        ]
        for step in (utility_architecture.architecture.selected_train_steps if utility_architecture else [])
    ]
    utility_package_rows = [
        [
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

    sections = [
        "## Annexures",
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
        "### Specialist Decision Fabric",
        markdown_table(["Packet", "Specialist", "Selected", "Critic Status"], agent_packet_rows or [["n/a", "n/a", "n/a", "n/a"]]),
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
        "### Mechanical Design Table",
        markdown_table(["Equipment", "Type", "Shell t (mm)", "Head t (mm)", "Nozzle (mm)", "Support", "Support t (mm)", "Load (kN)", "Thermal Growth (mm)", "Reinforcement (mm2)"], mechanical_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
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
        "### Equipment Cost Breakdown",
        markdown_table(["Equipment", "Type", "Bare Cost (INR)", "Installed Cost (INR)", "Spares (INR)", "Basis"], equipment_cost_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Plant Cost Summary",
        markdown_table(["Equipment", "Bare", "Installation", "Piping", "Instrumentation", "Total Installed"], plant_cost_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Scenario Comparison Table",
        markdown_table(["Scenario", "Utility Cost (INR/y)", "Operating Cost (INR/y)", "Revenue (INR/y)", "Gross Margin (INR/y)"], scenario_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Multi-Year Financial Schedule",
        markdown_table(["Year", "Capacity Utilization (%)", "Revenue (INR)", "Operating Cost (INR)", "Interest (INR)", "Depreciation (INR)", "PBT (INR)", "Tax (INR)", "PAT (INR)", "Cash Accrual (INR)"], schedule_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Typed Financial Schedule",
        markdown_table(["Year", "Capacity Utilization (%)", "Revenue", "Opex", "PBT", "Cash Accrual"], financial_schedule_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Debt Schedule",
        markdown_table(["Year", "Opening Debt", "Principal", "Interest", "Closing Debt"], debt_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Heat Integration Cases",
        markdown_table(["Route", "Case ID", "Title", "Recovered Duty (kW)", "Residual Hot Utility (kW)", "Annual Savings (INR)", "Payback (y)", "Feasible"], heat_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Utility Architecture",
        markdown_table(["Case", "Topology", "Recovered Duty (kW)", "Residual Hot Utility (kW)", "Exchanger Count"], utility_architecture_rows or [["n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Selected Utility Train",
        markdown_table(["Exchanger", "Topology", "Service", "Hot Unit", "Cold Unit", "Recovered Duty (kW)", "Medium"], utility_train_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
        "",
        "### Utility Train Packages",
        markdown_table(["Step", "Equipment", "Role", "Family", "Type", "Service", "Design Temp (C)", "Design Pressure (bar)", "Volume (m3)", "Duty (kW)", "Power (kW)", "Flow (m3/h)", "LMTD (K)", "Area (m2)", "Phase Load (kg/h)"], utility_package_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
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
        "### Process Design Datasheet",
        markdown_table(["Equipment", "Service", "Design Temp (C)", "Design Pressure (bar)", "Volume (m3)", "MoC"], datasheet_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]),
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
            ] if mechanical_design_basis else [["n/a", "n/a"]],
        ),
        "",
        "### Tax and Depreciation Basis",
        tax_depreciation_basis.markdown if tax_depreciation_basis else "No tax/depreciation basis captured.",
        "",
        "### Equipment Datasheet Bundle",
        equipment_datasheets_markdown or "No equipment datasheet bundle captured.",
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
