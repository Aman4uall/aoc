from __future__ import annotations

from aoc.models import (
    DecisionRecord,
    HeatIntegrationStudyArtifact,
    RouteChemistryArtifact,
    RouteSelectionComparisonArtifact,
    RouteSelectionComparisonRow,
    RouteSelectionArtifact,
    RouteSurveyArtifact,
    RoughAlternativeSummaryArtifact,
)
from aoc.route_families import RouteFamilyArtifact, profile_for_route


def _top_gap_labels(selected_breakdown: dict[str, float], candidate_breakdown: dict[str, float]) -> list[str]:
    deltas = [
        (selected_breakdown[key] - candidate_breakdown.get(key, 0.0), key)
        for key in selected_breakdown
    ]
    deltas.sort(reverse=True)
    return [label for delta, label in deltas if delta > 0.5][:2]


def build_route_selection_comparison(
    route_survey: RouteSurveyArtifact,
    route_chemistry: RouteChemistryArtifact,
    route_selection: RouteSelectionArtifact,
    route_decision: DecisionRecord,
    rough_summary: RoughAlternativeSummaryArtifact,
    heat_study: HeatIntegrationStudyArtifact,
    route_families: RouteFamilyArtifact | None = None,
) -> RouteSelectionComparisonArtifact:
    route_lookup = {route.route_id: route for route in route_survey.routes}
    graph_lookup = {graph.route_id: graph for graph in route_chemistry.route_graphs}
    rough_lookup = {case.route_id: case for case in rough_summary.cases}
    heat_lookup = {decision.route_id: decision for decision in heat_study.route_decisions}
    selected_alternative = next(
        (item for item in route_decision.alternatives if item.candidate_id == route_selection.selected_route_id),
        None,
    )
    selected_breakdown = selected_alternative.score_breakdown if selected_alternative is not None else {}
    rows: list[RouteSelectionComparisonRow] = []
    for alternative in route_decision.alternatives:
        route = route_lookup.get(alternative.candidate_id)
        if route is None:
            continue
        graph = graph_lookup.get(route.route_id)
        rough_case = rough_lookup.get(route.route_id)
        heat_case = heat_lookup.get(route.route_id)
        profile = profile_for_route(route_families, route.route_id) if route_families is not None else None
        selected = route.route_id == route_selection.selected_route_id
        rejection_reasons = list(alternative.rejected_reasons)
        why_not_chosen = ""
        if not selected and alternative.feasible:
            gap_labels = _top_gap_labels(selected_breakdown, alternative.score_breakdown)
            why_not_chosen = (
                f"Outscored by `{route_selection.selected_route_id}` on "
                + (", ".join(gap_labels) if gap_labels else "overall route ranking")
                + "."
            )
        elif not selected and not alternative.feasible:
            why_not_chosen = "Rejected by hard route constraints before final selection."
        rows.append(
            RouteSelectionComparisonRow(
                route_id=route.route_id,
                route_name=route.name,
                route_origin=route.route_origin,
                route_family_id=profile.route_family_id if profile is not None else (rough_case.route_family_id if rough_case is not None else ""),
                total_score=alternative.total_score,
                evidence_score=route.evidence_score,
                chemistry_completeness_score=(
                    graph.chemistry_completeness_score
                    if graph is not None
                    else route.chemistry_completeness_score
                ),
                separation_complexity_score=route.separation_complexity_score,
                selected_heat_case_id=alternative.outputs.get("selected_heat_case", ""),
                feasible=alternative.feasible,
                scientific_status=alternative.outputs.get("scientific_status", "design_feasible"),
                blocking_scientific_gate=alternative.outputs.get("blocking_scientific_gate", ""),
                selected=selected,
                rejection_reasons=rejection_reasons,
                why_not_chosen=why_not_chosen,
                citations=route.citations + alternative.citations,
                assumptions=route.assumptions + alternative.assumptions,
            )
        )
    rows.sort(key=lambda item: (item.selected, item.total_score), reverse=True)
    markdown = "\n".join(
        [
            "| Route | Origin | Family | Score | Evidence | Chemistry | Scientific Status | Selected | Rejection / Why not chosen |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {row.route_name} | {row.route_origin} | {row.route_family_id or '-'} | {row.total_score:.2f} | "
                f"{row.evidence_score:.2f} | {row.chemistry_completeness_score:.2f} | {row.scientific_status} | "
                f"{'yes' if row.selected else 'no'} | "
                f"{'; '.join(row.rejection_reasons) or row.why_not_chosen or row.blocking_scientific_gate or '-'} |"
                for row in rows
            ],
        ]
    )
    return RouteSelectionComparisonArtifact(
        selected_route_id=route_selection.selected_route_id,
        rows=rows,
        blocked_route_ids=sorted(
            {
                row.route_id
                for row in rows
                if not row.feasible
            }
        ),
        markdown=markdown,
        citations=sorted({source_id for row in rows for source_id in row.citations}),
        assumptions=route_decision.assumptions + route_selection.assumptions,
    )
