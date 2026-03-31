from __future__ import annotations

from aoc.models import (
    DocumentFactArtifact,
    PropertyDemandItem,
    PropertyDemandPlan,
    ReactionStep,
    RouteCandidateGraph,
    RouteChemistryArtifact,
    RouteSurveyArtifact,
    SensitivityLevel,
    SpeciesNode,
    SpeciesPropertyCoverage,
    SpeciesResolutionIssue,
)
from aoc.properties.sources import normalize_chemical_name
from aoc.properties.models import PropertyPackageArtifact


_PLACEHOLDER_NAMES = {"a", "b", "p", "product", "reactant", "intermediate"}
_CORE_PROPERTY_STAGE_MAP: dict[str, list[tuple[str, bool, SensitivityLevel, str]]] = {
    "thermodynamic_feasibility": [
        ("molecular_weight", True, SensitivityLevel.HIGH, "Identity anchor for route thermodynamics."),
        ("normal_boiling_point", True, SensitivityLevel.HIGH, "Needed for separation and volatility screening."),
        ("melting_point", False, SensitivityLevel.MEDIUM, "Needed for solids/handling screening."),
    ],
    "energy_balance": [
        ("liquid_density", True, SensitivityLevel.HIGH, "Needed for flow conversion and duty basis."),
        ("liquid_heat_capacity", True, SensitivityLevel.HIGH, "Needed for sensible-duty calculations."),
        ("heat_of_vaporization", True, SensitivityLevel.HIGH, "Needed for latent-duty calculations."),
    ],
    "reactor_design": [
        ("liquid_density", True, SensitivityLevel.HIGH, "Needed for reactor sizing."),
        ("liquid_viscosity", True, SensitivityLevel.HIGH, "Needed for hydraulic and heat-transfer screening."),
        ("thermal_conductivity", False, SensitivityLevel.MEDIUM, "Improves heat-transfer screening."),
    ],
    "distillation_design": [
        ("liquid_density", True, SensitivityLevel.HIGH, "Needed for separation hydraulics."),
        ("liquid_viscosity", True, SensitivityLevel.HIGH, "Needed for separation hydraulics."),
        ("liquid_heat_capacity", True, SensitivityLevel.HIGH, "Needed for thermal design."),
    ],
}


def _is_placeholder_species(name: str, formula: str | None) -> bool:
    normalized = normalize_chemical_name(name)
    if normalized in _PLACEHOLDER_NAMES:
        return True
    if normalized.startswith("generic_"):
        return True
    if normalized in {"document_reactants", "document_products"}:
        return True
    return False


def _species_nodes_for_route(route, document_lookup: dict[str, DocumentFactArtifact]) -> tuple[list[SpeciesNode], list[SpeciesResolutionIssue], list[str]]:
    nodes: dict[str, SpeciesNode] = {}
    issues: list[SpeciesResolutionIssue] = []
    anonymous_core_species: list[str] = []
    source_document_ids = [route.source_document_id] if route.source_document_id else []

    for participant in route.participants:
        species_id = normalize_chemical_name(participant.name)
        if _is_placeholder_species(participant.name, participant.formula):
            resolution_status = "anonymous"
        elif not (participant.formula or "").strip():
            resolution_status = "partial"
        else:
            resolution_status = "resolved"
        node = nodes.get(species_id)
        if node is None:
            node = SpeciesNode(
                species_id=species_id,
                canonical_name=participant.name,
                formula=participant.formula or None,
                aliases=[participant.name],
                role_tags=[participant.role],
                route_ids=[route.route_id],
                phase_hint=participant.phase or "",
                source_document_ids=source_document_ids,
                resolution_status=resolution_status,
                citations=route.citations,
            )
            nodes[species_id] = node
        else:
            if participant.name not in node.aliases:
                node.aliases.append(participant.name)
            if participant.role not in node.role_tags:
                node.role_tags.append(participant.role)
            if route.route_id not in node.route_ids:
                node.route_ids.append(route.route_id)
            if not node.formula and participant.formula:
                node.formula = participant.formula
            if resolution_status == "anonymous":
                node.resolution_status = "anonymous"
        if resolution_status == "anonymous" and participant.role in {"reactant", "product"}:
            anonymous_core_species.append(participant.name)
            issues.append(
                SpeciesResolutionIssue(
                    issue_id=f"{route.route_id}_{species_id}_anonymous",
                    route_id=route.route_id,
                    species_name=participant.name,
                    issue_code="anonymous_core_species",
                    blocking=True,
                    message=f"Route '{route.route_id}' still carries anonymous or formula-free core species '{participant.name}'.",
                    citations=route.citations,
                )
            )

    document = document_lookup.get(route.source_document_id or "")
    if document is not None:
        extracted_species = set(route.extracted_species)
        extracted_species.update(
            item
            for comparison in document.process_comparisons
            for option in comparison.options
            if option.option_id == route.route_id or option.label == route.name
            for item in option.extracted_species
        )
        for species_name in sorted(extracted_species):
            species_id = normalize_chemical_name(species_name)
            if species_id in nodes:
                continue
            nodes[species_id] = SpeciesNode(
                species_id=species_id,
                canonical_name=species_name,
                aliases=[species_name],
                role_tags=["document_mention"],
                route_ids=[route.route_id],
                source_document_ids=[document.source_id],
                resolution_status="partial",
                citations=document.citations,
            )
    return list(nodes.values()), issues, sorted(set(anonymous_core_species))


def build_route_chemistry_artifact(route_survey: RouteSurveyArtifact, document_facts: list[DocumentFactArtifact]) -> RouteChemistryArtifact:
    document_lookup = {item.source_id: item for item in document_facts}
    route_graphs: list[RouteCandidateGraph] = []
    resolved_species: set[str] = set()
    anonymous_species_count = 0
    blocking_route_ids: list[str] = []

    for route in route_survey.routes:
        species_nodes, issues, anonymous_core_species = _species_nodes_for_route(route, document_lookup)
        resolved_species.update(node.species_id for node in species_nodes if node.resolution_status != "anonymous")
        anonymous_species_count += len(anonymous_core_species)
        if issues:
            blocking_route_ids.append(route.route_id)
        step = ReactionStep(
            step_id=f"{route.route_id}_step_1",
            route_id=route.route_id,
            step_label="primary_route_step",
            reaction_family=(route.reaction_family_hints[0] if route.reaction_family_hints else ""),
            reactant_species_ids=[normalize_chemical_name(item.name) for item in route.participants if item.role == "reactant"],
            product_species_ids=[normalize_chemical_name(item.name) for item in route.participants if item.role == "product"],
            byproduct_species_ids=[normalize_chemical_name(item.name) for item in route.participants if item.role == "byproduct"],
            catalyst_names=list(route.catalysts),
            solvent_names=[],
            source_document_id=route.source_document_id or "",
            source_excerpt=route.rationale[:240],
            confidence=max(route.evidence_score, route.chemistry_completeness_score, 0.45),
            citations=route.citations,
        )
        completeness = route.chemistry_completeness_score
        if completeness <= 0:
            completeness = max(0.0, 1.0 - (len(anonymous_core_species) / max(len(species_nodes), 1)))
        route_graphs.append(
            RouteCandidateGraph(
                route_id=route.route_id,
                route_name=route.name,
                route_origin=route.route_origin,
                source_document_id=route.source_document_id,
                species_nodes=species_nodes,
                reaction_steps=[step],
                major_separation_hints=list(route.separations),
                anonymous_core_species=anonymous_core_species,
                unresolved_issues=issues,
                chemistry_completeness_score=completeness,
                batch_capable="batch" in " ".join(route.reaction_family_hints + route.separations + [route.name]).lower(),
                markdown=f"{route.name}: {len(species_nodes)} species nodes, {len(issues)} chemistry issues.",
                citations=route.citations,
                assumptions=route.assumptions,
            )
        )

    markdown = "\n".join(
        [
            "| Route | Origin | Species | Anonymous Core Species | Completeness |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {graph.route_name} | {graph.route_origin} | {len(graph.species_nodes)} | "
                f"{', '.join(graph.anonymous_core_species) or '-'} | {graph.chemistry_completeness_score:.2f} |"
                for graph in route_graphs
            ],
        ]
    )
    return RouteChemistryArtifact(
        route_graphs=route_graphs,
        resolved_species_count=len(resolved_species),
        anonymous_species_count=anonymous_species_count,
        blocking_route_ids=sorted(set(blocking_route_ids)),
        markdown=markdown,
        citations=sorted({source_id for route in route_survey.routes for source_id in route.citations}),
        assumptions=["Route chemistry graphs are synthesized from route participants and document-derived species mentions."],
    )


def build_property_demand_plan(route_chemistry: RouteChemistryArtifact, property_packages: PropertyPackageArtifact) -> PropertyDemandPlan:
    package_index = {package.identifier.identifier_id: package for package in property_packages.packages}
    items: list[PropertyDemandItem] = []
    coverage: list[SpeciesPropertyCoverage] = []
    blocked_stage_ids: set[str] = set()
    blocking_species_ids: set[str] = set()

    route_ids = [graph.route_id for graph in route_chemistry.route_graphs]
    for graph in route_chemistry.route_graphs:
        for node in graph.species_nodes:
            if "document_mention" in node.role_tags:
                continue
            package = package_index.get(node.species_id)
            for stage_id, stage_entries in _CORE_PROPERTY_STAGE_MAP.items():
                for property_name, blocking, sensitivity, rationale in stage_entries:
                    demand_id = f"{graph.route_id}_{node.species_id}_{stage_id}_{property_name}"
                    items.append(
                        PropertyDemandItem(
                            demand_id=demand_id,
                            species_id=node.species_id,
                            species_name=node.canonical_name,
                            stage_id=stage_id,
                            property_name=property_name,
                            sensitivity=sensitivity,
                            blocking=blocking,
                            rationale=rationale,
                            citations=node.citations,
                        )
                    )
                    prop = getattr(package, property_name, None) if package is not None else None
                    if prop is None:
                        status = "missing"
                        sources: list[str] = []
                    elif prop.blocking or prop.resolution_status == "blocked":
                        status = "blocked"
                        sources = list(prop.source_ids)
                    elif prop.resolution_status == "estimated":
                        status = "estimated"
                        sources = list(prop.source_ids)
                    else:
                        status = "covered"
                        sources = list(prop.source_ids)
                    coverage.append(
                        SpeciesPropertyCoverage(
                            coverage_id=demand_id,
                            species_id=node.species_id,
                            species_name=node.canonical_name,
                            stage_id=stage_id,
                            property_name=property_name,
                            coverage_status=status,
                            source_ids=sources,
                            blocking=blocking and status in {"missing", "blocked"},
                            rationale=rationale,
                            citations=sources or node.citations,
                        )
                    )
                    if blocking and status in {"missing", "blocked"}:
                        blocked_stage_ids.add(stage_id)
                        blocking_species_ids.add(node.species_id)

    markdown = "\n".join(
        [
            "| Species | Stage | Property | Coverage | Blocking |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {item.species_name} | {item.stage_id} | {item.property_name} | {item.coverage_status} | {'yes' if item.blocking else 'no'} |"
                for item in coverage
            ],
        ]
    )
    return PropertyDemandPlan(
        route_ids=route_ids,
        items=items,
        coverage=coverage,
        blocking_species_ids=sorted(blocking_species_ids),
        blocked_stage_ids=sorted(blocked_stage_ids),
        markdown=markdown,
        citations=sorted({source_id for package in property_packages.packages for source_id in package.citations}),
        assumptions=["Property demand planning is derived from route-chemistry species nodes and stage-critical property requirements."],
    )
