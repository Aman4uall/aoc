from __future__ import annotations

from collections import defaultdict

from aoc.models import (
    DocumentFactArtifact,
    FlowsheetBlueprintArtifact,
    FlowsheetBlueprintStep,
    ProcessNarrativeArtifact,
    RecycleIntentArtifact,
    RouteChemistryArtifact,
    RouteOption,
    RouteSurveyArtifact,
    SeparationDutyItem,
    UnitTrainCandidateSet,
)
from aoc.route_families import RouteFamilyArtifact, profile_for_route


def _route_graph_lookup(route_chemistry: RouteChemistryArtifact):
    return {graph.route_id: graph for graph in route_chemistry.route_graphs}


def _document_lookup(document_facts: list[DocumentFactArtifact]):
    return {document.source_id: document for document in document_facts}


def _equipment_tag_pools(document: DocumentFactArtifact | None) -> dict[str, list[str]]:
    pools: dict[str, list[str]] = defaultdict(list)
    if document is None:
        return pools
    for mention in document.equipment_mentions:
        pools[mention.unit_type or "other"].append(mention.unit_tag)
    return pools


def _take_tag(pools: dict[str, list[str]], *types: str) -> str:
    for equipment_type in types:
        tags = pools.get(equipment_type, [])
        if tags:
            return tags.pop(0)
    return ""


def _primary_separation_family(route: RouteOption, profile) -> str:
    text = " ".join(route.separations + [profile.primary_separation_train if profile is not None else ""]).lower()
    if "absor" in text or "strip" in text:
        return "absorption"
    if "extract" in text:
        return "extraction"
    if "crystal" in text or "filter" in text:
        return "crystallization"
    if "evapor" in text or "concentr" in text:
        return "evaporation"
    if "dry" in text:
        return "drying"
    if "flash" in text or "phase split" in text:
        return "flash"
    if "distill" in text or "column" in text:
        return "distillation"
    return "separation"


def _reactor_unit_type(route: RouteOption, profile, batch_capable: bool, pools: dict[str, list[str]]) -> tuple[str, str]:
    reactor_basis = (profile.primary_reactor_class if profile is not None else "").lower()
    if pools.get("plug_flow_reactor") or "plug" in reactor_basis or "pfr" in reactor_basis:
        return "plug_flow_reactor", _take_tag(pools, "plug_flow_reactor", "reactor")
    if batch_capable:
        return "batch_stirred_reactor", _take_tag(pools, "reactor", "plug_flow_reactor")
    if "fixed" in reactor_basis:
        return "fixed_bed_reactor", _take_tag(pools, "reactor")
    return "cstr", _take_tag(pools, "reactor", "plug_flow_reactor")


def _needs_phase_split(route: RouteOption, separation_family: str, document: DocumentFactArtifact | None) -> bool:
    if separation_family in {"absorption", "extraction", "flash"}:
        return True
    if any(token in " ".join(route.separations).lower() for token in ("phase", "flash", "separator", "decant")):
        return True
    return bool(document and any(mention.unit_type == "separator" for mention in document.equipment_mentions))


def _append_step(
    steps: list[FlowsheetBlueprintStep],
    route: RouteOption,
    section_id: str,
    section_label: str,
    step_role: str,
    unit_id: str,
    solver_anchor_unit_id: str,
    unit_type: str,
    service: str,
    *,
    unit_tag: str = "",
    reaction_step_ref: str = "",
    separation_basis_ref: str = "",
    batch_campaign_ref: str = "",
    phase_basis: str = "",
    notes: list[str] | None = None,
) -> None:
    steps.append(
        FlowsheetBlueprintStep(
            step_id=unit_id,
            route_id=route.route_id,
            section_id=section_id,
            section_label=section_label,
            step_role=step_role,
            unit_id=unit_id,
            solver_anchor_unit_id=solver_anchor_unit_id,
            unit_tag=unit_tag,
            unit_type=unit_type,
            service=service,
            reaction_step_ref=reaction_step_ref,
            separation_basis_ref=separation_basis_ref,
            batch_campaign_ref=batch_campaign_ref,
            phase_basis=phase_basis,
            upstream_step_ids=[steps[-1].step_id] if steps else [],
            notes=notes or [],
            citations=route.citations,
            assumptions=route.assumptions,
        )
    )


def _build_blueprint_for_route(
    route: RouteOption,
    route_chemistry: RouteChemistryArtifact,
    route_families: RouteFamilyArtifact | None,
    document_facts: list[DocumentFactArtifact],
    operating_mode: str,
) -> FlowsheetBlueprintArtifact:
    graph = _route_graph_lookup(route_chemistry).get(route.route_id)
    profile = profile_for_route(route_families, route.route_id) if route_families is not None else None
    document = _document_lookup(document_facts).get(route.source_document_id or "")
    pools = _equipment_tag_pools(document)
    batch_capable = bool(graph.batch_capable) if graph is not None else operating_mode == "batch"
    separation_family = _primary_separation_family(route, profile)
    reaction_steps = graph.reaction_steps if graph is not None and graph.reaction_steps else []
    steps: list[FlowsheetBlueprintStep] = []
    duties: list[SeparationDutyItem] = []
    recycle_intents: list[RecycleIntentArtifact] = []

    _append_step(
        steps,
        route,
        "feed_handling",
        "Feed handling",
        "feed_preparation",
        "feed_prep",
        "feed_prep",
        "feed_preparation",
        "Feed preparation and charging",
        unit_tag=_take_tag(pools, "mixer"),
        phase_basis="feed conditioning",
        notes=["Initial route-derived charging and premix step."],
    )

    reactor_unit_type, reactor_tag = _reactor_unit_type(route, profile, batch_capable, pools)
    _append_step(
        steps,
        route,
        "reaction",
        "Reaction",
        "reaction",
        "reactor",
        "reactor",
        reactor_unit_type,
        "Primary reaction step",
        unit_tag=reactor_tag,
        reaction_step_ref=reaction_steps[0].step_id if reaction_steps else "",
        batch_campaign_ref="batch_campaign_main" if batch_capable else "",
        phase_basis="reaction step",
        notes=[profile.primary_reactor_class if profile is not None else "Route-derived reactor basis."],
    )

    if _needs_phase_split(route, separation_family, document):
        _append_step(
            steps,
            route,
            "phase_split",
            "Phase split",
            "phase_split",
            "primary_flash",
            "primary_flash",
            "phase_separator",
            "Primary quench and phase split",
            unit_tag=_take_tag(pools, "separator"),
            phase_basis="vapor-liquid or liquid-liquid split",
            notes=["Inserted because the route/separation family implies an explicit split before purification."],
        )

    _append_step(
        steps,
        route,
        "primary_recovery",
        "Primary recovery",
        "primary_separation",
        "primary_separation",
        "primary_separation",
        separation_family,
        "Primary separation train",
        unit_tag=_take_tag(pools, "distillation_column_or_condenser", "separator", "evaporator"),
        separation_basis_ref=separation_family,
        phase_basis=separation_family,
        notes=[profile.primary_separation_train if profile is not None else "Route-derived primary separation."],
    )
    duties.append(
        SeparationDutyItem(
            duty_id=f"{route.route_id}_primary_sep",
            route_id=route.route_id,
            step_id="primary_separation",
            separation_family=separation_family,
            driving_force="phase equilibrium" if separation_family in {"distillation", "flash", "absorption", "extraction"} else "solid-liquid split",
            key_species=[item.name for item in route.participants[:3]],
            basis=profile.primary_separation_train if profile is not None else separation_family,
            citations=route.citations,
            assumptions=route.assumptions,
        )
    )

    if separation_family in {"distillation", "evaporation", "absorption", "extraction"}:
        _append_step(
            steps,
            route,
            "purification",
            "Purification",
            "purification",
            "purification",
            "purification",
            "purification_train",
            "Purification and finishing train",
            unit_tag=_take_tag(pools, "distillation_column_or_condenser", "separator", "evaporator"),
            separation_basis_ref="product purification",
            phase_basis="product finishing",
            notes=["Route-derived purification section downstream of primary recovery."],
        )

    if separation_family == "crystallization":
        _append_step(
            steps,
            route,
            "solids_finishing",
            "Solids finishing",
            "filtration",
            "filtration",
            "filtration",
            "filtration",
            "Filtration and mother-liquor split",
            unit_tag=_take_tag(pools, "separator"),
            separation_basis_ref="filtration",
            phase_basis="solid-liquid split",
            notes=["Added for crystallization-led route handling."],
        )
        _append_step(
            steps,
            route,
            "solids_finishing",
            "Solids finishing",
            "drying",
            "drying",
            "drying",
            "drying",
            "Drying and solids finishing",
            unit_tag=_take_tag(pools, "other"),
            separation_basis_ref="drying",
            phase_basis="moisture removal",
            notes=["Added for crystallization-led route handling."],
        )

    needs_regeneration = any(token in " ".join(route.separations + route.byproducts).lower() for token in ("recycle", "recovery", "regeneration"))
    if profile is not None and profile.route_family_id in {"regeneration_loop_train", "extraction_recovery_train"}:
        needs_regeneration = True
    if route.catalysts or needs_regeneration:
        _append_step(
            steps,
            route,
            "recycle_recovery",
            "Recycle recovery",
            "recycle_recovery",
            "recycle_recovery",
            "recycle_recovery",
            "recycle_recovery",
            "Recycle and catalyst/solvent recovery",
            unit_tag=_take_tag(pools, "separator", "distillation_column_or_condenser"),
            phase_basis="recycle closure",
            notes=["Inserted because the route implies catalyst/solvent recovery or recycle closure."],
        )
        recycle_intents.append(
            RecycleIntentArtifact(
                intent_id=f"{route.route_id}_recycle_to_reactor",
                route_id=route.route_id,
                source_step_id="recycle_recovery",
                target_step_id="reactor",
                stream_family="solvent_or_catalyst_recycle",
                basis="Recover reusable route species back to the primary reactor section.",
                closing_species=[item.name for item in route.participants if item.role == "reactant"][:2],
                citations=route.citations,
                assumptions=route.assumptions,
            )
        )

    _append_step(
        steps,
        route,
        "storage",
        "Storage and dispatch",
        "storage",
        "storage",
        "storage",
        "storage",
        "Product storage and dispatch",
        unit_tag="",
        phase_basis="product dispatch",
        notes=["Terminal storage step for report-level topology."],
    )

    if route.byproducts or route.hazards:
        _append_step(
            steps,
            route,
            "waste_management",
            "Waste handling",
            "waste_treatment",
            "waste_treatment",
            "waste_treatment",
            "waste_handling",
            "Waste and purge handling",
            unit_tag="",
            phase_basis="waste and purge control",
            notes=["Added because the route carries byproduct or hazard handling burdens."],
        )

    markdown = "\n".join(
        [
            "| Step | Section | Role | Unit Type | Tag | Solver Anchor | Upstream |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *[
                f"| {step.unit_id} | {step.section_label} | {step.step_role} | {step.unit_type} | {step.unit_tag or '-'} | "
                f"{step.solver_anchor_unit_id or '-'} | {', '.join(step.upstream_step_ids) or '-'} |"
                for step in steps
            ],
        ]
    )
    return FlowsheetBlueprintArtifact(
        blueprint_id=f"{route.route_id}_blueprint",
        route_id=route.route_id,
        route_name=route.name,
        route_origin=route.route_origin,
        steps=steps,
        separation_duties=duties,
        recycle_intents=recycle_intents,
        batch_capable=batch_capable,
        selected_unit_tags=[step.unit_tag for step in steps if step.unit_tag],
        markdown=markdown,
        citations=route.citations + (graph.citations if graph is not None else []),
        assumptions=route.assumptions + ["Flowsheet blueprint is a route-derived conceptual train synthesized before detailed material-balance solving."],
    )


def build_unit_train_candidate_set(
    route_survey: RouteSurveyArtifact,
    route_chemistry: RouteChemistryArtifact,
    route_families: RouteFamilyArtifact | None,
    document_facts: list[DocumentFactArtifact],
    operating_mode: str,
) -> UnitTrainCandidateSet:
    blueprints = [
        _build_blueprint_for_route(route, route_chemistry, route_families, document_facts, operating_mode)
        for route in route_survey.routes
    ]
    markdown = "\n".join(
        [
            "| Route | Steps | Tagged Units | Recycle Intents |",
            "| --- | --- | --- | --- |",
            *[
                f"| {blueprint.route_name} | {len(blueprint.steps)} | {', '.join(blueprint.selected_unit_tags) or '-'} | {len(blueprint.recycle_intents)} |"
                for blueprint in blueprints
            ],
        ]
    )
    return UnitTrainCandidateSet(
        blueprints=blueprints,
        markdown=markdown,
        citations=sorted({source_id for blueprint in blueprints for source_id in blueprint.citations}),
        assumptions=["Unit-train candidates are synthesized from route chemistry, route family, and document equipment mentions."],
    )


def select_flowsheet_blueprint(candidate_set: UnitTrainCandidateSet, route_id: str) -> FlowsheetBlueprintArtifact:
    for blueprint in candidate_set.blueprints:
        if blueprint.route_id == route_id:
            return blueprint
    raise RuntimeError(f"No flowsheet blueprint candidate found for route '{route_id}'.")


def build_process_narrative_from_blueprint(blueprint: FlowsheetBlueprintArtifact) -> ProcessNarrativeArtifact:
    mermaid_lines = ["graph TD"]
    for step in blueprint.steps:
        label_bits = [step.service]
        if step.unit_tag:
            label_bits.append(f"({step.unit_tag})")
        mermaid_lines.append(f'  {step.step_id}["{"<br/>".join(label_bits)}"]')
    for step in blueprint.steps:
        for upstream in step.upstream_step_ids:
            mermaid_lines.append(f"  {upstream} --> {step.step_id}")
    for recycle in blueprint.recycle_intents:
        mermaid_lines.append(f"  {recycle.source_step_id} -. recycle .-> {recycle.target_step_id}")
    markdown = "\n".join(
        [
            f"Route-derived process narrative for `{blueprint.route_name}`.",
            "",
            "### Route-to-Unit Mapping",
            "",
            blueprint.markdown,
            "",
            "### Separation Duty Register",
            "",
            (
                "\n".join(
                    [
                        "| Step | Family | Driving Force | Key Species | Basis |",
                        "| --- | --- | --- | --- | --- |",
                        *[
                            f"| {item.step_id} | {item.separation_family} | {item.driving_force or '-'} | "
                            f"{', '.join(item.key_species) or '-'} | {item.basis or '-'} |"
                            for item in blueprint.separation_duties
                        ],
                    ]
                )
                if blueprint.separation_duties
                else "No explicit separation duties were synthesized."
            ),
            "",
            "### Recycle Intent Register",
            "",
            (
                "\n".join(
                    [
                        "| Source | Target | Stream Family | Closing Species | Basis |",
                        "| --- | --- | --- | --- | --- |",
                        *[
                            f"| {item.source_step_id} | {item.target_step_id} | {item.stream_family or '-'} | "
                            f"{', '.join(item.closing_species) or '-'} | {item.basis or '-'} |"
                            for item in blueprint.recycle_intents
                        ],
                    ]
                )
                if blueprint.recycle_intents
                else "No explicit recycle intents were synthesized."
            ),
        ]
    )
    return ProcessNarrativeArtifact(
        bfd_mermaid="\n".join(mermaid_lines),
        markdown=markdown,
        citations=blueprint.citations,
        assumptions=blueprint.assumptions,
    )
