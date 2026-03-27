from __future__ import annotations

from aoc.models import (
    ProcessTemplate,
    ProjectBasis,
    ReactionSystem,
    RouteOption,
    SensitivityLevel,
    StreamTable,
)
from aoc.solvers.composition import build_unit_composition_artifacts
from aoc.solvers.flowsheet_sequence import build_generic_sequence_streams
from aoc.value_engine import make_value_record


def _hourly_output_kg(basis: ProjectBasis) -> float:
    return basis.capacity_tpa * 1000.0 / (basis.annual_operating_days * 24.0)


def build_stream_table_generic(
    basis: ProjectBasis,
    route: RouteOption,
    reaction_system: ReactionSystem,
    citations: list[str],
    assumptions: list[str],
) -> StreamTable:
    solve_result = build_generic_sequence_streams(
        product_mass_kg_hr=_hourly_output_kg(basis),
        route=route,
        reaction_system=reaction_system,
        citations=citations,
        assumptions=assumptions,
    )
    composition_states, composition_closures = build_unit_composition_artifacts(
        solve_result.streams,
        solve_result.unit_operation_packets,
        citations,
        assumptions,
    )
    extra_assumptions = [
        "Generic material-balance engine uses a sequence-based flowsheet solver with explicit feed preparation, reaction, staged separations, recycle, and purge handling.",
        f"Sequence family inferred as `{solve_result.sequence_family}` from route separations and expanded into the stage path: {', '.join(solve_result.stage_labels)}.",
        "Unitwise composition propagation now aggregates solved inlet and outlet component state for each major unit before energy and equipment sizing.",
    ]
    if basis.process_template == ProcessTemplate.ETHYLENE_GLYCOL_INDIA:
        extra_assumptions.append("Ethylene glycol cases retain strong water recycle inside the generic sequence solver to reflect dilution-intensive hydration practice.")
    return StreamTable(
        streams=solve_result.streams,
        closure_error_pct=solve_result.closure_error_pct,
        calc_traces=solve_result.calc_traces,
        value_records=[
            make_value_record(
                "stream_product_mass_flow",
                "Product mass flow",
                _hourly_output_kg(basis),
                "kg/h",
                citations=citations,
                assumptions=assumptions + extra_assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "stream_total_feed_mass",
                "Total fresh-feed mass flow",
                solve_result.total_fresh_feed_mass_kg_hr,
                "kg/h",
                citations=citations,
                assumptions=assumptions + extra_assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "stream_total_external_out",
                "Total external outlet mass flow",
                solve_result.total_external_out_mass_kg_hr,
                "kg/h",
                citations=citations,
                assumptions=assumptions + extra_assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
            make_value_record(
                "stream_closure_error",
                "Mass-balance closure error",
                solve_result.closure_error_pct,
                "%",
                citations=citations,
                assumptions=assumptions + extra_assumptions,
                sensitivity=SensitivityLevel.HIGH,
            ),
        ],
        composition_states=composition_states,
        composition_closures=composition_closures,
        unit_operation_packets=solve_result.unit_operation_packets,
        phase_split_specs=solve_result.phase_split_specs,
        separator_performances=solve_result.separator_performances,
        separation_packets=solve_result.separation_packets,
        recycle_packets=solve_result.recycle_packets,
        convergence_summaries=solve_result.convergence_summaries,
        citations=citations,
        assumptions=assumptions + extra_assumptions,
    )
