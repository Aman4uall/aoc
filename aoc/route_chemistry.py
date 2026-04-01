from __future__ import annotations

import re

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
from aoc.properties.sources import is_valid_property_identifier_name
from aoc.properties.sources import match_benchmark_entry
from aoc.properties.sources import normalize_chemical_name
from aoc.properties.models import PropertyPackageArtifact


_PLACEHOLDER_NAMES = {"a", "b", "p", "product", "reactant", "intermediate"}
_INVALID_CORE_SPECIES_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)?%?|\d+(?:\.\d+)?\.)\s*$")
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


def _is_valid_species_name(name: str) -> bool:
    stripped = name.strip()
    if not stripped:
        return False
    if _INVALID_CORE_SPECIES_RE.match(stripped):
        return False
    if len(re.findall(r"[A-Za-z]", stripped)) < 2:
        return False
    lowered = stripped.lower()
    if "%" in lowered and not any(token in lowered for token in ("acid", "oxide", "benzene", "alcohol", "amine", "hydrogen", "oxygen", "water", "ibuprofen")):
        return False
    return True


def _is_placeholder_species(name: str, formula: str | None) -> bool:
    normalized = normalize_chemical_name(name)
    if normalized in _PLACEHOLDER_NAMES:
        return True
    if normalized.startswith("generic_"):
        return True
    if normalized in {"document_reactants", "document_products"}:
        return True
    return False


def _route_product_id(route) -> str:
    for participant in route.participants:
        if participant.role == "product":
            return normalize_chemical_name(participant.name)
    return ""


def _is_benzalkonium_route(route) -> bool:
    text = " ".join(
        [
            route.route_id,
            route.name,
            route.reaction_equation,
            " ".join(route.separations),
            " ".join(route.byproducts),
            " ".join(getattr(route, "solvents", [])),
        ]
    ).lower()
    return _route_product_id(route) == "benzalkonium_chloride" or "benzalkonium" in text or "quaternization" in text


def _species_kind_for_name(route, species_name: str, role_tags: set[str]) -> tuple[str, str, str]:
    species_id = normalize_chemical_name(species_name)
    if _is_benzalkonium_route(route):
        if species_id == "benzalkonium_chloride":
            return "bundle", "active_bundle", "nonvolatile"
        if species_id == "alkyldimethylamine":
            return "bundle", "feed_bundle", "semivolatile"
        if species_id in {"water", "ethanol"}:
            return "carrier", "carrier_component", "carrier"
        if species_id == "benzyl_chloride":
            return "discrete", "residual_critical", "volatile"
        if species_id == "benzyl_alcohol":
            return "discrete", "light_end_impurity", "semivolatile"
        if species_id == "hydrogen_chloride":
            return "discrete", "acidic_offgas", "volatile"
        if "impurity_class" in role_tags:
            return "impurity_class", "impurity_class", "unknown"
    if "impurity_class" in role_tags:
        return "impurity_class", "impurity_class", "unknown"
    if "solvent" in role_tags:
        return "carrier", "solvent", "volatile"
    return "discrete", "", "unknown"


def _annotate_species_node(route, node: SpeciesNode) -> SpeciesNode:
    role_tags = set(node.role_tags)
    kind, commercial_role, volatility_class = _species_kind_for_name(route, node.canonical_name, role_tags)
    phase_hint = node.phase_hint
    if _is_benzalkonium_route(route) and node.species_id == "benzalkonium_chloride":
        phase_hint = phase_hint or "liquid_solution"
        role_tags.update({"active_bundle", "solution_product", "nonvolatile_active", "quaternary_salt"})
    elif _is_benzalkonium_route(route) and node.species_id == "alkyldimethylamine":
        role_tags.update({"amine_feed_bundle", "recoverable_reagent"})
    elif _is_benzalkonium_route(route) and node.species_id == "benzyl_chloride":
        role_tags.update({"toxic_residual", "volatile_light_end"})
    elif _is_benzalkonium_route(route) and node.species_id == "benzyl_alcohol":
        role_tags.update({"light_end_impurity"})
    elif _is_benzalkonium_route(route) and node.species_id in {"water", "ethanol"}:
        role_tags.update({"carrier", "solvent"})
    return node.model_copy(
        update={
            "role_tags": sorted(role_tags),
            "phase_hint": phase_hint,
            "species_kind": kind,
            "commercial_role": commercial_role,
            "volatility_class": volatility_class,
        }
    )


def _upsert_species_node(
    nodes: dict[str, SpeciesNode],
    *,
    route,
    species_name: str,
    role: str,
    source_document_ids: list[str],
    citations: list[str],
    formula: str | None = None,
    phase_hint: str = "",
    resolution_status: str = "partial",
) -> None:
    if not _is_valid_species_name(species_name):
        return
    species_id = normalize_chemical_name(species_name)
    benchmark_key, benchmark_record = match_benchmark_entry(species_name, formula)
    resolved_formula = formula or (str(benchmark_record.get("formula")) if benchmark_record else None)
    if benchmark_record and resolved_formula:
        resolution_status = "resolved"
    existing = nodes.get(species_id)
    if existing is None:
        node = SpeciesNode(
            species_id=species_id,
            canonical_name=species_name,
            formula=resolved_formula or None,
            aliases=[species_name],
            role_tags=[role],
            route_ids=[route.route_id],
            phase_hint=phase_hint,
            source_document_ids=source_document_ids,
            resolution_status=resolution_status,
            citations=citations,
        )
        nodes[species_id] = _annotate_species_node(route, node)
        return
    aliases = list(existing.aliases)
    if species_name not in aliases:
        aliases.append(species_name)
    role_tags = list(existing.role_tags)
    if role not in role_tags:
        role_tags.append(role)
    updated = existing.model_copy(
        update={
            "aliases": aliases,
            "role_tags": role_tags,
            "formula": existing.formula or resolved_formula,
            "phase_hint": existing.phase_hint or phase_hint,
            "resolution_status": existing.resolution_status if existing.resolution_status == "resolved" else resolution_status,
        }
    )
    nodes[species_id] = _annotate_species_node(route, updated)


def _augment_special_route_species(
    route,
    nodes: dict[str, SpeciesNode],
    source_document_ids: list[str],
) -> None:
    if not _is_benzalkonium_route(route):
        return
    for solvent_name in getattr(route, "solvents", []):
        _upsert_species_node(
            nodes,
            route=route,
            species_name=solvent_name,
            role="solvent",
            source_document_ids=source_document_ids,
            citations=route.citations,
        )
    byproduct_text = " ".join(route.byproducts).lower()
    if "benzyl alcohol" in byproduct_text:
        _upsert_species_node(
            nodes,
            route=route,
            species_name="Benzyl alcohol",
            role="byproduct",
            source_document_ids=source_document_ids,
            citations=route.citations,
        )
    if "residual free amine" in byproduct_text:
        _upsert_species_node(
            nodes,
            route=route,
            species_name="Alkyldimethylamine",
            role="residual_impurity",
            source_document_ids=source_document_ids,
            citations=route.citations,
        )
    if "residual benzyl chloride" in byproduct_text:
        _upsert_species_node(
            nodes,
            route=route,
            species_name="Benzyl chloride",
            role="residual_impurity",
            source_document_ids=source_document_ids,
            citations=route.citations,
        )
    if "color bodies" in byproduct_text:
        _upsert_species_node(
            nodes,
            route=route,
            species_name="Color bodies",
            role="impurity_class",
            source_document_ids=source_document_ids,
            citations=route.citations,
            resolution_status="partial",
        )
    if any(token in byproduct_text for token in ("aqueous chloride purge", "water/alcohol trim blend", "active dilution")):
        _upsert_species_node(
            nodes,
            route=route,
            species_name="Water",
            role="carrier",
            source_document_ids=source_document_ids,
            citations=route.citations,
        )


def _species_nodes_for_route(route, document_lookup: dict[str, DocumentFactArtifact]) -> tuple[list[SpeciesNode], list[SpeciesResolutionIssue], list[str]]:
    nodes: dict[str, SpeciesNode] = {}
    issues: list[SpeciesResolutionIssue] = []
    anonymous_core_species: list[str] = []
    source_document_ids = [route.source_document_id] if route.source_document_id else []

    for participant in route.participants:
        if not _is_valid_species_name(participant.name):
            if participant.role in {"reactant", "product"}:
                anonymous_core_species.append(participant.name)
                issues.append(
                    SpeciesResolutionIssue(
                        issue_id=f"{route.route_id}_{normalize_chemical_name(participant.name) or 'invalid'}_invalid",
                        route_id=route.route_id,
                        species_name=participant.name,
                        issue_code="invalid_core_species",
                        blocking=True,
                        message=f"Route '{route.route_id}' carries invalid core species token '{participant.name}'.",
                        citations=route.citations,
                    )
                )
            continue
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
            nodes[species_id] = _annotate_species_node(route, node)
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
            nodes[species_id] = _annotate_species_node(route, node)
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

    _augment_special_route_species(route, nodes, source_document_ids)

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
        extracted_species.update(
            item
            for mention in document.reaction_mentions
            if mention.route_option_id == route.route_id
            for item in (mention.reactants + mention.products + mention.byproducts + mention.solvents + mention.catalysts)
        )
        for species_name in sorted(extracted_species):
            if not _is_valid_species_name(species_name):
                continue
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
            nodes[species_id] = _annotate_species_node(route, nodes[species_id])
    return list(nodes.values()), issues, sorted(set(anonymous_core_species))


def _reaction_steps_for_route(route, document_lookup: dict[str, DocumentFactArtifact]) -> list[ReactionStep]:
    document = document_lookup.get(route.source_document_id or "")
    if document is not None:
        mentions = [item for item in document.reaction_mentions if item.route_option_id == route.route_id]
        if mentions:
            steps: list[ReactionStep] = []
            for index, mention in enumerate(mentions, start=1):
                steps.append(
                    ReactionStep(
                        step_id=mention.mention_id or f"{route.route_id}_step_{index}",
                        route_id=route.route_id,
                        step_label=mention.step_label or f"document_step_{index}",
                        reaction_family=mention.reaction_family_hint or (route.reaction_family_hints[0] if route.reaction_family_hints else ""),
                        reactant_species_ids=[normalize_chemical_name(item) for item in mention.reactants],
                        product_species_ids=[normalize_chemical_name(item) for item in mention.products],
                        byproduct_species_ids=[normalize_chemical_name(item) for item in mention.byproducts],
                        catalyst_names=list(mention.catalysts),
                        solvent_names=list(mention.solvents or getattr(route, "solvents", [])),
                        source_document_id=mention.source_document_id,
                        source_excerpt=mention.source_excerpt,
                        confidence=max(route.evidence_score, route.chemistry_completeness_score, 0.45),
                        citations=mention.citations,
                    )
                )
            return steps
    return [
        ReactionStep(
            step_id=f"{route.route_id}_step_1",
            route_id=route.route_id,
            step_label="primary_route_step",
            reaction_family=(route.reaction_family_hints[0] if route.reaction_family_hints else ""),
            reactant_species_ids=[normalize_chemical_name(item.name) for item in route.participants if item.role == "reactant"],
            product_species_ids=[normalize_chemical_name(item.name) for item in route.participants if item.role == "product"],
            byproduct_species_ids=[normalize_chemical_name(item.name) for item in route.participants if item.role == "byproduct"],
            catalyst_names=list(route.catalysts),
            solvent_names=list(getattr(route, "solvents", [])),
            source_document_id=route.source_document_id or "",
            source_excerpt=route.rationale[:240],
            confidence=max(route.evidence_score, route.chemistry_completeness_score, 0.45),
            citations=route.citations,
        )
    ]


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
        steps = _reaction_steps_for_route(route, document_lookup)
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
                reaction_steps=steps,
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
            if not is_valid_property_identifier_name(node.canonical_name):
                continue
            package = package_index.get(node.species_id)
            if package is None:
                continue
            for stage_id, stage_entries in _stage_entries_for_node(node, package).items():
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
                    prop = getattr(package, property_name, None)
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


def _float_property_value(package: PropertyPackageArtifact | object, field: str) -> float | None:
    prop = getattr(package, field, None)
    if prop is None:
        return None
    try:
        return float(prop.value)
    except Exception:
        return None


def _stage_entries_for_node(
    node: SpeciesNode,
    package: object,
) -> dict[str, list[tuple[str, bool, SensitivityLevel, str]]]:
    entries = {stage_id: list(stage_entries) for stage_id, stage_entries in _CORE_PROPERTY_STAGE_MAP.items()}
    role_tags = set(node.role_tags)
    product_only = "product" in role_tags and "reactant" not in role_tags and "byproduct" not in role_tags
    catalyst_like = "catalyst" in role_tags
    active_solution_bundle = node.commercial_role == "active_bundle" or "nonvolatile_active" in role_tags
    carrier_component = node.commercial_role == "carrier_component" or "carrier" in role_tags
    melting_point_c = _float_property_value(package, "melting_point")
    boiling_point_c = _float_property_value(package, "normal_boiling_point")
    likely_nonvolatile_solid = product_only and (
        (melting_point_c is not None and melting_point_c >= 35.0)
        or (boiling_point_c is not None and boiling_point_c >= 220.0)
    )

    if catalyst_like:
        return {
            "thermodynamic_feasibility": [
                ("molecular_weight", True, SensitivityLevel.HIGH, "Catalyst identity still needs molecular-weight anchoring."),
                ("melting_point", False, SensitivityLevel.MEDIUM, "Catalyst physical state improves handling and storage screening."),
            ]
        }

    if active_solution_bundle:
        return {
            "thermodynamic_feasibility": [
                ("molecular_weight", True, SensitivityLevel.HIGH, "Representative active-bundle identity anchors the commercial solution basis."),
                ("liquid_density", True, SensitivityLevel.HIGH, "Needed for active-solution handling and concentration calculations."),
                ("liquid_viscosity", True, SensitivityLevel.HIGH, "Needed for liquid-service hydraulic and mixing screening."),
                ("liquid_heat_capacity", False, SensitivityLevel.MEDIUM, "Improves solution-service sensible-duty calculations."),
            ],
            "energy_balance": [
                ("liquid_density", True, SensitivityLevel.HIGH, "Needed for active-solution flow conversion."),
                ("liquid_heat_capacity", True, SensitivityLevel.HIGH, "Needed for active-solution sensible-duty calculations."),
            ],
            "reactor_design": [
                ("liquid_density", True, SensitivityLevel.HIGH, "Needed for liquid-phase quaternization sizing."),
                ("liquid_viscosity", True, SensitivityLevel.HIGH, "Needed for agitation and hydraulic screening."),
                ("liquid_heat_capacity", False, SensitivityLevel.MEDIUM, "Improves exotherm and hold-up screening."),
            ],
            "distillation_design": [],
        }

    if carrier_component:
        entries["reactor_design"] = [
            ("liquid_density", True, SensitivityLevel.HIGH, "Needed for carrier and solvent handling."),
            ("liquid_viscosity", True, SensitivityLevel.HIGH, "Needed for carrier hydraulic screening."),
        ]

    if likely_nonvolatile_solid:
        entries["energy_balance"] = []
        entries["reactor_design"] = []
        entries["distillation_design"] = []
    elif product_only:
        entries["reactor_design"] = []
    return entries
