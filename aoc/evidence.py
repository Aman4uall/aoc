from __future__ import annotations

from collections import defaultdict

from aoc.models import (
    GeographicScope,
    PropertyEstimate,
    ProjectConfig,
    PropertyGapArtifact,
    ProvenanceTag,
    ResearchBundle,
    ResolvedSourceSet,
    ResolvedValue,
    ResolvedValueArtifact,
    SensitivityLevel,
    SourceCandidate,
    SourceCandidateSet,
    SourceConflict,
    SourceDomain,
    SourceKind,
    ValueRecord,
)


SOURCE_KIND_AUTHORITY = {
    SourceKind.GOVERNMENT: 1.00,
    SourceKind.HANDBOOK: 0.95,
    SourceKind.COMPANY_REPORT: 0.90,
    SourceKind.LITERATURE: 0.88,
    SourceKind.PATENT: 0.84,
    SourceKind.SDS: 0.82,
    SourceKind.UTILITY: 0.82,
    SourceKind.LOGISTICS: 0.78,
    SourceKind.MARKET: 0.75,
    SourceKind.WEB: 0.70,
    SourceKind.USER_DOCUMENT: 0.68,
}

SOURCE_DOMAIN_PRIORITY = [
    SourceDomain.TECHNICAL,
    SourceDomain.SAFETY,
    SourceDomain.MARKET,
    SourceDomain.SITE,
    SourceDomain.UTILITIES,
    SourceDomain.LOGISTICS,
    SourceDomain.REGULATORY,
    SourceDomain.ECONOMICS,
]

RESOLUTION_LEVELS = {
    ProvenanceTag.SOURCED: 1,
    ProvenanceTag.USER_SUPPLIED: 1,
    ProvenanceTag.CALCULATED: 2,
    ProvenanceTag.ESTIMATED: 3,
    ProvenanceTag.ANALOGY: 4,
}


def _year_score(reference_year: int | None, target_year: int) -> float:
    if reference_year is None:
        return 0.45
    gap = abs(target_year - reference_year)
    if gap <= 1:
        return 1.00
    if gap <= 3:
        return 0.85
    if gap <= 5:
        return 0.65
    return 0.40


def _geography_score(config: ProjectConfig, source) -> float:
    if not config.require_india_only_data:
        return 0.90 if source.geographic_scope != GeographicScope.UNKNOWN else 0.60
    if source.country and source.country.lower() == "india":
        return 1.00
    if source.geographic_scope in {GeographicScope.INDIA, GeographicScope.STATE, GeographicScope.CITY}:
        return 1.00
    return 0.10


def _consistency_score(source) -> float:
    score = 0.5
    if source.extraction_snippet:
        score += 0.2
    if source.citation_text:
        score += 0.1
    if source.url_or_doi or source.local_path:
        score += 0.1
    score += max(0.0, min(0.1, (source.confidence - 0.5) * 0.2))
    return min(score, 1.0)


def _property_estimates_from_values(values: list[ResolvedValue]) -> list[PropertyEstimate]:
    estimates: list[PropertyEstimate] = []
    for value in values:
        if value.provenance_method in {ProvenanceTag.SOURCED, ProvenanceTag.USER_SUPPLIED} and not value.blocking:
            continue
        estimates.append(
            PropertyEstimate(
                estimate_id=f"{value.value_id}_estimate",
                property_name=value.name,
                selected_method=value.provenance_method,
                candidate_methods=[
                    ProvenanceTag.SOURCED,
                    ProvenanceTag.CALCULATED,
                    ProvenanceTag.ESTIMATED,
                    ProvenanceTag.ANALOGY,
                ],
                selected_source_id=value.selected_source_id,
                sensitivity=value.sensitivity,
                blocking=value.blocking,
                rationale=value.justification or "Estimate carried from the resolution hierarchy.",
                citations=value.citations,
                assumptions=value.assumptions,
            )
        )
    return estimates


def _merge_property_estimates(*groups: list[PropertyEstimate]) -> list[PropertyEstimate]:
    merged: dict[str, PropertyEstimate] = {}
    for group in groups:
        for estimate in group:
            merged[estimate.estimate_id] = estimate
    return sorted(merged.values(), key=lambda item: item.property_name.lower())


def build_resolved_source_set(config: ProjectConfig, bundle: ResearchBundle) -> ResolvedSourceSet:
    grouped = defaultdict(list)
    for source in bundle.sources:
        grouped[source.source_domain].append(source)
    groups: list[SourceCandidateSet] = []
    conflicts: list[SourceConflict] = []
    unresolved_conflicts: list[str] = []
    selected_source_ids: list[str] = []
    for domain in SOURCE_DOMAIN_PRIORITY:
        sources = list(grouped.get(domain, []))
        if not sources and domain == SourceDomain.MARKET:
            sources = list(grouped.get(SourceDomain.ECONOMICS, []))
        if not sources and domain == SourceDomain.ECONOMICS:
            sources = list(grouped.get(SourceDomain.MARKET, []))
        candidates: list[SourceCandidate] = []
        target_year = config.basis.economic_reference_year if domain in {
            SourceDomain.MARKET,
            SourceDomain.ECONOMICS,
            SourceDomain.UTILITIES,
            SourceDomain.LOGISTICS,
            SourceDomain.SITE,
            SourceDomain.REGULATORY,
        } else config.basis.utility_basis_year
        for source in sources:
            authority = SOURCE_KIND_AUTHORITY.get(source.source_kind, 0.65)
            recency = _year_score(source.reference_year or source.normalization_year, target_year)
            geography = _geography_score(config, source)
            domain_fit = 1.0
            consistency = _consistency_score(source)
            total = 100.0 * (
                0.32 * authority
                + 0.18 * recency
                + 0.22 * geography
                + 0.18 * domain_fit
                + 0.10 * consistency
            )
            candidates.append(
                SourceCandidate(
                    source_id=source.source_id,
                    authority_score=authority * 100.0,
                    recency_score=recency * 100.0,
                    geography_score=geography * 100.0,
                    domain_fit_score=domain_fit * 100.0,
                    consistency_score=consistency * 100.0,
                    total_score=total,
                    rationale=f"{source.source_kind.value}/{source.source_domain.value} scored for authority, year fit, and India relevance.",
                )
            )
        candidates.sort(key=lambda item: item.total_score, reverse=True)
        selected_ids = [item.source_id for item in candidates[:2]]
        unresolved = False
        score_gap = 0.0
        if len(candidates) > 1:
            score_gap = round(candidates[0].total_score - candidates[1].total_score, 3)
        if config.require_india_only_data and domain in {
            SourceDomain.MARKET,
            SourceDomain.SITE,
            SourceDomain.UTILITIES,
            SourceDomain.LOGISTICS,
            SourceDomain.REGULATORY,
            SourceDomain.ECONOMICS,
        } and selected_ids:
            best_source = next(source for source in bundle.sources if source.source_id == selected_ids[0])
            unresolved = _geography_score(config, best_source) < 0.5
        if domain in {SourceDomain.TECHNICAL, SourceDomain.MARKET, SourceDomain.SITE, SourceDomain.ECONOMICS} and not candidates:
            unresolved = True
        if unresolved:
            unresolved_conflicts.append(domain.value)
        if len(candidates) > 1 and (score_gap <= 5.0 or unresolved):
            conflicts.append(
                SourceConflict(
                    conflict_id=f"{domain.value}_conflict",
                    source_domain=domain,
                    selected_source_id=selected_ids[0] if selected_ids else None,
                    competing_source_ids=[candidate.source_id for candidate in candidates[1:3]],
                    score_gap=score_gap,
                    blocking=unresolved,
                    rationale="Top-ranked sources remain close in score or fail the India-only requirement.",
                    recommended_resolution="Prefer the highest-ranked India-grounded source or request analyst confirmation if the score gap remains narrow.",
                    citations=selected_ids,
                    assumptions=["Source conflict recorded when top-ranked evidence remains close or non-India-grounded."],
                )
            )
        selected_source_ids.extend(selected_ids)
        rows = [
            f"| {candidate.source_id} | {candidate.total_score:.1f} | {candidate.authority_score:.1f} | {candidate.recency_score:.1f} | {candidate.geography_score:.1f} |"
            for candidate in candidates
        ]
        markdown = "\n".join(
            [
                "| Source | Total | Authority | Recency | Geography |",
                "| --- | --- | --- | --- | --- |",
                *rows,
            ]
        ) if rows else "No candidates available."
        groups.append(
            SourceCandidateSet(
                group_id=f"{domain.value}_sources",
                source_domain=domain,
                geographic_requirement="India" if config.require_india_only_data else "global-or-india",
                candidates=candidates,
                selected_source_ids=selected_ids,
                unresolved_conflict=unresolved,
                markdown=markdown,
                citations=selected_ids,
                assumptions=[
                    "Source ranking uses deterministic authority, recency, geography, domain-fit, and consistency heuristics."
                ],
            )
        )
    lines = ["| Domain | Selected Sources | Conflict |", "| --- | --- | --- |"]
    for group in groups:
        lines.append(
            f"| {group.source_domain.value} | {', '.join(group.selected_source_ids) or 'none'} | {'yes' if group.unresolved_conflict else 'no'} |"
        )
    return ResolvedSourceSet(
        groups=groups,
        selected_source_ids=sorted(dict.fromkeys(selected_source_ids)),
        unresolved_conflicts=sorted(set(unresolved_conflicts)),
        conflicts=conflicts,
        markdown="\n".join(lines),
        citations=sorted(dict.fromkeys(selected_source_ids)),
        assumptions=["Resolved-source selection is deterministic and public-data-only oriented."],
    )


def build_resolved_value_artifact(
    property_gap: PropertyGapArtifact,
    source_resolution: ResolvedSourceSet,
    config: ProjectConfig,
) -> ResolvedValueArtifact:
    selected_source_ids = set(source_resolution.selected_source_ids)
    resolved_values: list[ResolvedValue] = []
    unresolved_value_ids: list[str] = []
    for value in property_gap.values:
        selected_source_id = next((source_id for source_id in value.source_ids if source_id in selected_source_ids), None)
        resolution_level = RESOLUTION_LEVELS.get(value.provenance_method, 5)
        status = "blocked" if value.blocking else ("estimated" if value.provenance_method in {ProvenanceTag.ESTIMATED, ProvenanceTag.ANALOGY, ProvenanceTag.CALCULATED} else "resolved")
        justification = (
            "Resolved from ranked public sources."
            if selected_source_id
            else "No ranked source matched this value directly; it relies on its original provenance chain."
        )
        resolved = ResolvedValue(
            value_id=value.value_id,
            name=value.name,
            value=value.value,
            units=value.units,
            provenance_method=value.provenance_method,
            source_ids=value.source_ids,
            uncertainty_band=value.uncertainty_band,
            sensitivity=value.sensitivity,
            blocking=value.blocking,
            resolution_level=resolution_level,
            selected_source_id=selected_source_id,
            resolution_status=status,
            justification=justification,
            citations=value.citations,
            assumptions=value.assumptions,
        )
        if config.uncertainty_policy.high_sensitivity_blocks and resolved.sensitivity == SensitivityLevel.HIGH and (
            resolved.blocking or resolved.resolution_status == "blocked"
        ):
            unresolved_value_ids.append(resolved.value_id)
        resolved_values.append(resolved)
    lines = [
        "| Value | Level | Status | Sensitivity | Selected Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for value in resolved_values:
        lines.append(
            f"| {value.name} | {value.resolution_level} | {value.resolution_status} | {value.sensitivity.value} | {value.selected_source_id or 'none'} |"
        )
    return ResolvedValueArtifact(
        values=resolved_values,
        unresolved_value_ids=sorted(set(unresolved_value_ids)),
        property_estimates=_merge_property_estimates(_property_estimates_from_values(resolved_values)),
        markdown="\n".join(lines),
        citations=sorted({source_id for value in resolved_values for source_id in value.source_ids}),
        assumptions=property_gap.assumptions,
    )


def extend_resolved_value_artifact(
    existing: ResolvedValueArtifact,
    value_records: list[ValueRecord],
    source_resolution: ResolvedSourceSet,
    config: ProjectConfig,
    context: str,
) -> ResolvedValueArtifact:
    selected_source_ids = set(source_resolution.selected_source_ids)
    value_index = {value.value_id: value for value in existing.values}
    unresolved_value_ids = set(existing.unresolved_value_ids)
    for value in value_records:
        selected_source_id = next((source_id for source_id in value.source_ids if source_id in selected_source_ids), None)
        resolution_level = RESOLUTION_LEVELS.get(value.provenance_method, 5)
        status = "blocked" if value.blocking else ("estimated" if value.provenance_method in {ProvenanceTag.ESTIMATED, ProvenanceTag.ANALOGY, ProvenanceTag.CALCULATED} else "resolved")
        resolved = ResolvedValue(
            value_id=value.value_id,
            name=value.name,
            value=value.value,
            units=value.units,
            provenance_method=value.provenance_method,
            source_ids=value.source_ids,
            uncertainty_band=value.uncertainty_band,
            sensitivity=value.sensitivity,
            blocking=value.blocking,
            resolution_level=resolution_level,
            selected_source_id=selected_source_id,
            resolution_status=status,
            justification=f"{context}: {'matched ranked source' if selected_source_id else 'retained provenance chain only'}.",
            citations=value.citations,
            assumptions=value.assumptions,
        )
        value_index[resolved.value_id] = resolved
        if config.uncertainty_policy.high_sensitivity_blocks and resolved.sensitivity == SensitivityLevel.HIGH and (
            resolved.blocking or resolved.resolution_status == "blocked"
        ):
            unresolved_value_ids.add(resolved.value_id)
        elif resolved.value_id in unresolved_value_ids and not resolved.blocking and resolved.resolution_status != "blocked":
            unresolved_value_ids.discard(resolved.value_id)
    values = sorted(value_index.values(), key=lambda item: item.name.lower())
    lines = [
        "| Value | Level | Status | Sensitivity | Selected Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for value in values:
        lines.append(
            f"| {value.name} | {value.resolution_level} | {value.resolution_status} | {value.sensitivity.value} | {value.selected_source_id or 'none'} |"
        )
    return ResolvedValueArtifact(
        values=values,
        unresolved_value_ids=sorted(unresolved_value_ids),
        property_estimates=_merge_property_estimates(existing.property_estimates, _property_estimates_from_values(values)),
        markdown="\n".join(lines),
        citations=sorted({source_id for value in values for source_id in value.source_ids}),
        assumptions=existing.assumptions + [f"Resolved values extended with {context}."],
    )
