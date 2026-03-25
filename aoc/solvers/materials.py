from __future__ import annotations

from aoc.models import (
    ProcessTemplate,
    ProjectBasis,
    ReactionSystem,
    RouteOption,
    SensitivityLevel,
    StreamTable,
)
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
        conversion_fraction=reaction_system.conversion_fraction,
        selectivity_fraction=reaction_system.selectivity_fraction,
        excess_ratio=reaction_system.excess_ratio,
        citations=citations,
        assumptions=assumptions,
    )
    extra_assumptions = [
        "Generic material-balance engine uses a sequence-based flowsheet solver with explicit feed preparation, reaction, staged separations, recycle, and purge handling.",
        f"Sequence family inferred as `{solve_result.sequence_family}` from route separations and expanded into the stage path: {', '.join(solve_result.stage_labels)}.",
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
        unit_operation_packets=solve_result.unit_operation_packets,
        separation_packets=solve_result.separation_packets,
        recycle_packets=solve_result.recycle_packets,
        citations=citations,
        assumptions=assumptions + extra_assumptions,
    )
